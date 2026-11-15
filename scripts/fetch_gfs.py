#!/usr/bin/env python3
"""Fetch NOAA GFS 0.25-degree pressure-level winds for two approximate reference locations.
No extrapolation, no operational go/no-go decision. Uses ecCodes Python bindings.
"""
import datetime as dt
import json
import math
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from eccodes import codes_grib_new_from_file, codes_get, codes_grib_find_nearest, codes_release

BASE="https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
LOCATIONS={"kirishima":{"name":"霧島演習場周辺（暫定）","lat":31.98,"lon":130.76},
           "tanegashima":{"name":"南種子町周辺（暫定）","lat":30.38,"lon":130.90}}
LEVELS=[1000,975,950,925,900,850,800,750,700,650,600,550,500]
HOURS=[3,6,12,24,36,48,60,72]

def download(cycle, hour):
    file=f"gfs.t{cycle.hour:02d}z.pgrb2.0p25.f{hour:03d}"
    query={"file":file,"dir":f"/gfs.{cycle:%Y%m%d}/{cycle.hour:02d}/atmos",
           "var_UGRD":"on","var_VGRD":"on","var_HGT":"on",
           "subregion":"","leftlon":"130.25","rightlon":"131.25",
           "toplat":"32.50","bottomlat":"29.90"}
    for lev in LEVELS:query[f"lev_{lev}_mb"]="on"
    url=BASE+"?"+urllib.parse.urlencode(query)
    req=urllib.request.Request(url,headers={"User-Agent":"freefall-weather/0.2 (educational weather dashboard)"})
    with urllib.request.urlopen(req,timeout=90) as response:
        data=response.read(20_000_001)
    if len(data)>20_000_000 or not data.startswith(b"GRIB"):
        raise ValueError("Not a valid bounded GRIB2 download")
    return data

def parse(data):
    fields={}
    with tempfile.NamedTemporaryFile(suffix=".grib2") as tmp:
        tmp.write(data);tmp.flush()
        with open(tmp.name,"rb") as f:
            while True:
                gid=codes_grib_new_from_file(f)
                if gid is None:break
                try:
                    name=codes_get(gid,"shortName")
                    level=int(codes_get(gid,"level"))
                    if level not in LEVELS or name not in ("u","v","gh"):continue
                    for key,p in LOCATIONS.items():
                        nearest=codes_grib_find_nearest(gid,p["lat"],p["lon"])[0]
                        value=float(nearest["value"])
                        if math.isfinite(value):fields.setdefault(key,{}).setdefault(level,{})[name]=value
                finally:codes_release(gid)
    return fields

def make_record(fields,cycle,hour):
    valid=cycle+dt.timedelta(hours=hour)
    result={"valid_utc":valid.isoformat().replace("+00:00","Z"),"forecast_hour":hour,"locations":{}}
    for key,levels in fields.items():
        rows=[]
        for lev in LEVELS:
            v=levels.get(lev,{})
            if not all(k in v for k in ("u","v","gh")):continue
            u,w,h=v["u"],v["v"],v["gh"]
            if not 0<=h<=10000:continue
            rows.append({"pressure_hpa":lev,"geopotential_height_m_msl_approx":round(h),
                         "wind_direction_deg_from":round((math.degrees(math.atan2(-u,-w))+360)%360),
                         "wind_speed_ms":round(math.hypot(u,w),1)})
        result["locations"][key]=rows
    return result

def main():
    now=dt.datetime.now(dt.timezone.utc)
    # Use an older cycle to allow for publication delay; retry another cycle if missing.
    cycles=[(now-dt.timedelta(hours=lag)).replace(hour=0,minute=0,second=0,microsecond=0)
            for lag in (0,12,24)]
    cycles=list(dict.fromkeys(cycles))
    records=[];errors=[];chosen=None
    for cycle in cycles:
        try:
            data=download(cycle,3)
            first=make_record(parse(data),cycle,3)
            if not any(first["locations"].values()):raise ValueError("No complete U/V/HGT fields")
            chosen=cycle;records.append(first);break
        except Exception as exc:errors.append(f"{cycle.isoformat()}: {type(exc).__name__}: {exc}")
    if chosen:
        for hour in HOURS[1:]:
            try:
                r=make_record(parse(download(chosen,hour)),chosen,hour)
                if any(r["locations"].values()):records.append(r)
                else:errors.append(f"f{hour:03d}: no valid fields")
            except Exception as exc:errors.append(f"f{hour:03d}: {type(exc).__name__}: {exc}")
    payload={"schema_version":1,"source":"NOAA NCEP NOMADS GFS 0.25-degree GRIB filter",
             "source_url":BASE,"model":"GFS","cycle_utc":chosen.isoformat().replace("+00:00","Z") if chosen else None,
             "retrieved_utc":dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z"),
             "altitude_reference":"geopotential height, approximately MSL; NOT AGL",
             "confidence":"not independently verified","locations":LOCATIONS,"forecasts":records,
             "errors":errors[:16],"status":"ok" if records else "unavailable"}
    Path("data").mkdir(exist_ok=True)
    Path("data/gfs_winds.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"GFS: {len(records)} forecast times; status={payload['status']}; errors={len(errors)}")
    if not records:raise SystemExit("No valid NOAA GFS data. See data/gfs_winds.json")

if __name__=="__main__":main()
