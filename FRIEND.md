# Helping with a timing run

Thank you for lending your computer for an hour or two.

## What this is

This project tries to make a program that splits large numbers into their factors use as little work as possible. We measure how long different versions of the program take. Our own computer runs hot, which makes its timings jumpy, so a second computer tells us whether a speed-up is real or just our machine.

Your computer will run a few versions of the program, one after another, many times, and write down how long each one took. Nothing is installed system-wide except the usual programming tools (Python and Rust) if you don't already have them. Nothing is sent anywhere: at the end you get **one file**, and you send it back yourself.

## What you need

- A computer running **Linux**, or **Windows with WSL** (the Linux layer for Windows).
  - A Mac also works, but its timings are less steady; we will still use them.
- About 2 GB of free disk space.
- An internet connection for the first step.

## Step 1: set up (once, about 10 minutes)

Open a terminal and paste these two lines:

    curl -sSfO https://raw.githubusercontent.com/onojk/lumens-per-watt/main/tools/friend_setup.sh
    bash friend_setup.sh

It checks what is missing and **asks before installing anything**. If it needs your password (for "sudo"), it tells you why first. It ends with **PASS** or **FAIL**.
- If it says FAIL, copy the text on the screen and send it to us.

## Step 2: the run (about 30–90 minutes)

We will tell you the run's name. Then paste:

    cd ~/lumens-per-watt
    git pull
    tools/friend_run.sh <run-name>

While it runs:
- **Keep the computer plugged in.**
- **Leave it idle:** no browsing, games or video calls. Other programs disturb the timings.
- Don't let it go to sleep. Turning the screen off is fine.

It prints "replicate 1 of 8 done" and so on, then a short summary.

## Step 3: send the file back

The run finishes by naming one file, something like `results_<run-name>_<your-computer>_<date>.json`, in the `lumens-per-watt` folder. Email or message that file to us. That is all.

The file records your computer's processor model, number of cores, operating system, temperature and clock speed during the run, and the timings. It contains no personal files, passwords or browsing data.

## If something goes wrong

- **"REFUSED: … local changes":** something in the folder was edited. Run `git checkout .`, then try again.
- **The computer got hot or loud:** that is normal; the run uses one processor core flat out. The file records the temperature.
- **Anything else:** send us what the screen says.
