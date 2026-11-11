# Running on the Hetzner box

The collector runs once a day under its own unprivileged user, `hrjobs`, separate from the other collectors on
the box.

| Thing | Where |
|---|---|
| Clone | `/home/hrjobs/hr-jobs` |
| Schedule | `hr-jobs-daily.timer`, 05:30 UTC each day (an hour after the ai-jobs run) |
| Without a deploy key | Collect-only mode: results go to `/home/hrjobs/collected` and stay on the box |
| With a deploy key | Publishes `data/current/jobs.csv`, `data/summary/DATE.json`, `reports/DATE.md`, `reports/latest.md` to GitHub |
| Deploy key | `/home/hrjobs/.ssh/id_ed25519`, registered on this repo only, with write access. The repo owner adds it. |
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

## Turning on publishing

The box publishes once it holds a deploy key that can write to this repo. Make the key on the box:

```bash
ssh hetz 'sudo -u hrjobs mkdir -p -m 700 /home/hrjobs/.ssh && sudo -u hrjobs ssh-keygen -q -t ed25519 -N "" -f /home/hrjobs/.ssh/id_ed25519 -C hr-jobs-box && sudo cat /home/hrjobs/.ssh/id_ed25519.pub'
```

Add the printed line at github.com/nikbearbrown/hr-jobs/settings/keys with "Allow write access" ticked. Then
point the clone at SSH and trust GitHub's host key:

```bash
ssh hetz 'sudo -u hrjobs git -C /home/hrjobs/hr-jobs remote set-url origin git@github.com:nikbearbrown/hr-jobs.git && sudo -u hrjobs sh -c "ssh-keyscan -t ed25519 github.com > /home/hrjobs/.ssh/known_hosts"'
```

The next run copies what the box collected into the repo and pushes it.

## Installing from scratch

```bash
sudo adduser --disabled-password --gecos "" hrjobs
sudo -u hrjobs git clone https://github.com/nikbearbrown/hr-jobs.git /home/hrjobs/hr-jobs
sudo cp /home/hrjobs/hr-jobs/ops/hr-jobs-daily.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hr-jobs-daily.timer
```
