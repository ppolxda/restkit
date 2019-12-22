set BAT_PATH=%~dp0
set WORK_PATH=%~dp0../../../
set MDBS_PATH=%WORK_PATH%/mdbs
set MDBS_OUT_PATH=%WORK_PATH%/mdbs/out
set MDBS_SRC_PATH=%WORK_PATH%/mdbs/src

cd %WORK_PATH%
python3 -m restkit.gen.errors_trans.make_error_info --service=restkit --fs_in=./restkit/gen/errors_trans/error_info.csv --fs_out=./restkit/tools/error_info.py --fs_tmpl=${fpath}/error_info.jinja

