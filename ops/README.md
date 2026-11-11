# Running on the Hetzner box

The collector runs once a day under its own unprivileged user, `hrjobs`, separate from the other collectors on
the box.

| Thing | Where |
|---|---|
| Clone | `/home/hrjobs/hr-jobs` |
| Schedule | `hr-jobs-daily.timer`, 05:30 UTC each day (an hour after the ai-jobs run) |
| What it pushes | `data/current/jobs.csv`, `data/summary/DATE.json`, `reports/DATE.md`, `reports/latest.md` |
| Push access | A deploy key that can write to this repo only (`/home/hrjobs/.ssh/id_ed25519`) |
| USAJOBS key | `/home/hrjobs/.usajobs/key` and `/home/hrjobs/.usajobs/email`, mode 600. Without them the federal source is skipped and the report says "no key". |
| Adzuna key | `/home/hrjobs/.adzuna/app_id` and `/home/hrjobs/.adzuna/app_key`. Same rule. |

## Everyday commands

```bash
ssh hetz 'sudo journalctl -u hr-jobs-daily.service -n 40 --no-pager'
```

```bash
ssh hetz 'systemctl list-timers hr-jobs-daily.timer --no-pager'
```

Run it now instead of waiting for the timer:

```bash
ssh hetz 'sudo systemctl start hr-jobs-daily.service'
```

Stop the daily run without removing anything (delete the file to resume):

```bash
ssh hetz 'sudo -u hrjobs touch /home/hrjobs/STOP'
```

## Putting the USAJOBS key on the box

The key is never typed into a chat or committed. Copy the two files from the machine that has them:

```bash
ssh hetz 'sudo -u hrjobs mkdir -p -m 700 /home/hrjobs/.usajobs'
```

```bash
for f in key email; do ssh hetz "sudo -u hrjobs sh -c 'umask 077; cat > /home/hrjobs/.usajobs/$f'" < ~/.usajobs/$f; done
```

## Installing from scratch

```bash
sudo adduser --disabled-password --gecos "" hrjobs
sudo -u hrjobs ssh-keygen -t ed25519 -N "" -f /home/hrjobs/.ssh/id_ed25519 -C hr-jobs-box
# add /home/hrjobs/.ssh/id_ed25519.pub to the repo as a deploy key with write access, then:
sudo -u hrjobs git clone git@github.com:nikbearbrown/hr-jobs.git /home/hrjobs/hr-jobs
sudo cp /home/hrjobs/hr-jobs/ops/hr-jobs-daily.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hr-jobs-daily.timer
```
