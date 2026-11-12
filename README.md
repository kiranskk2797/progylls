# ProGylls

ProGylls is a responsive PM learning prototype. The two HTML pages use plain JavaScript and CSS. A Python server on your computer handles signup, login, session cookies and PM stage selection using SQLite. Answers, XP and progress are stored in the browser under the signed-in account’s ID. Use the same browser, server address, port and account database to resume. A new device does not automatically receive your progress.

## Start on Windows

1. Install Python 3 if needed. Open PowerShell and run `python --version` to check.
2. Open the project folder in File Explorer. For a fresh demo, use a fresh browser profile and double-click **Start ProGylls.cmd**. From PowerShell in this folder the equivalent command is `python .\progylls_server.py`.
3. Leave that window open and visit **http://localhost:8765**. To stop the server, press Ctrl+C in its window. The app works with system font fallbacks offline. Resource links and hosted fonts need internet access.

**Returning from the Downloads prototype:** stop the old server first. To keep your original account IDs, point this copy to the original account database folder before starting it. In PowerShell, from the new project folder:

```powershell
$env:PROGYLLS_DATA = Join-Path $env:USERPROFILE 'Downloads\Progylls Documentation-20261110T074213Z-1-001\.progylls-data'
python .\progylls_server.py
```

Open the same localhost address in the same browser profile and log in. Keep that database private. When starting from a fresh clone elsewhere, omit the variable to create a new local database. Password recovery requires the original server's mail configuration.

## Try the Swiggy case

1. Create an account, choose your PM stage, select **Continue to the tour**, then **Choose my first skill**.
2. Select **Product Thinking & Sense**. In the first guide, choose **Problem Framing · Swiggy checkout price shock**. Returning learners can open **Learn → Pre-Reads → Product Discovery → Problem Framing**.
3. Read the five steps, choose **Finish → Mark as read**, then **Swiggy checkout price shock · Quick Drill**. If an unlock notice opens, dismiss it to return to the guide.
4. Answer the four questions. For the branch exercise, tap an event on the left, then an outcome on the right. Use **Start retry** to revisit missed questions. Finish the drill and choose **Enter the Gym Room**.
5. Save your first investigation to reveal new evidence. Write your follow-up, rate it against the six rubric dimensions, and submit. Open **See a strong example**, then **Finish → View Progress**. The written case earns completion XP. Its rubric scores are your own ratings.

The drill is also under **Practice → Quick Drill → Mixed sets** and the case under **Practice → Case Simulations** once unlocked. Progress opens at 30 XP. Practice IDs are `qd-swiggy` and `gr-swiggy` under the existing `product` skill. The example is newly authored and the interview data are fictional.

[Curriculum and unlocks](docs/CURRICULUM.md) · [Further reading and exercises](docs/RESOURCES.md)
