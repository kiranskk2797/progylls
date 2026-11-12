# ProGylls

ProGylls is a gamified Product Management learning platform built around short lessons, practical drills, and case-based practice. This repository contains the existing HTML/Python prototype and a minimal React starter for future development. The prototype's two HTML pages use plain JavaScript and CSS; a local Python server handles signup, login, session cookies, and PM stage selection with SQLite. Answers, XP, and progress are stored in the browser under the signed-in account's ID. Use the same browser profile and account database to resume progress.

## Technology

- React and TypeScript, built and served locally with Vite
- Existing prototype: HTML, CSS, JavaScript, and a Python standard-library server
- SQLite for local prototype account data

## Requirements

- Node.js 22.12 or later (or Node.js 24 or later) and npm for the React starter
- Python 3 for the existing prototype

## Run the React starter

From the project directory:

```powershell
npm install
npm run dev
```

Open the local URL printed by Vite. To create and preview a production build:

```powershell
npm run build
npm run preview
```

## Run the existing prototype

In PowerShell, start the local server:

```powershell
python .\progylls_server.py
```

Then visit **http://localhost:8765**. You can also use **Start ProGylls.cmd** on Windows. To stop the server, press Ctrl+C. The app uses system font fallbacks offline; hosted fonts and resource links need internet access.

The server stores local account data under `.progylls-data/`; that directory is excluded from Git and should remain private. By default, a fresh clone creates a new local database. To reuse an existing local database, set `PROGYLLS_DATA` to its folder before starting the server. Password recovery requires the server's mail configuration.

## Explore the prototype

1. Create an account, choose your PM stage, select **Continue to the tour**, then **Choose my first skill**.
2. Select **Product Thinking & Sense**. In the first guide, choose **Problem Framing · Swiggy checkout price shock**. Returning learners can open **Learn → Pre-Reads → Product Discovery → Problem Framing**.
3. Read the five steps, choose **Finish → Mark as read**, then open **Swiggy checkout price shock · Quick Drill**. If an unlock notice opens, dismiss it to return to the guide.
4. Answer the four questions. For the branch exercise, tap an event on the left, then an outcome on the right. Use **Start retry** to revisit missed questions. Finish the drill and choose **Enter the Gym Room**.
5. Save your first investigation to reveal new evidence. Write your follow-up, rate it against the six rubric dimensions, and submit. Open **See a strong example**, then **Finish → View Progress**. The case earns completion XP; rubric scores are your own ratings.

The drill is also under **Practice → Quick Drill → Mixed sets** and the case under **Practice → Case Simulations** after unlocking. Progress opens at 30 XP. The practice IDs are `qd-swiggy` and `gr-swiggy` under the existing `product` skill. The interview data are fictional.

See the [curriculum and unlocks](docs/CURRICULUM.md) and [learning resources](docs/RESOURCES.md) for more detail.
