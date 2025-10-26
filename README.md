# OpenKeyFlow-BETA
**Free, open-source text expander for Windows, Mac and Linux.--BETA/INPRODUCTION**  

OpenKeyFlow lets you define custom text snippets that expand automatically as you type — ideal for quick replies, IT workflows, or any repetitive plaintext. Purpose-built, lightweight, secure, and built to stay free and open for everyone. 

---

## Features

-  **Instant expansion** — type a short trigger (e.g. `-email1`) and watch it expand immediately.  
-  **Persistent storage** — saves your hotkeys and expansions in a simple JSON file.  
-  **CSV import/export** — manage or share your hotkey lists easily from a CSV.  
-  **Autostart option** — run silently in your tray at login and startup.
-  **Local-only** — no network access, no data collection, built with 

---

## Getting Started

### Requirements
- Windows 10 or 11 
- Python 3.10+ (if running from source)  
- Or download the pre-built `.exe` from [Releases](#)

### Running from Source
1. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

   The requirements file uses platform markers, so the Windows-only
   dependency (`pywin32`) is skipped automatically on macOS and Linux.
   If the launcher still reports missing packages, confirm you installed
   them for the same interpreter you're using to run the app:

   ```bash
   python -m pip show PyQt5
   ```

   Replace `python` with the exact interpreter path if you work with
   multiple environments.

   pip install -r requirements.txt
   ```

2. Launch the GUI using whichever entry point is most convenient:

   ```bash
   # Standard console entry point
   python openkeyflow.py

   # Module form (works the same way)
   python -m app
   ```

   On Windows you can also double-click `OpenKeyFlow.pyw` after installing the
   requirements. The `.pyw` extension opens the GUI without spawning a console
   window, making it feel more like a native app shortcut. If a dependency is
   missing, launching `python openkeyflow.py` will point out exactly which
   package to install.
   window, making it feel more like a native app shortcut.

### Why I Built This
I wanted a text expander app that was fast, secure, lightweight and open source. I've been an avid user of tools like AutoHotKey and AutoText for many years. However, I wasn't interested in using these tools for scripting or automation and just needed an app to expand plaintext for IT ticket entries and repetitive emails. Because programs like this monitor your keyboard waiting for a trigger, using AutoHotKey or AutoText became less feasible for security reasons (i.e. they both have internet access, AutoText is closed source, AutoHotKey scripting can be used malciously and remotely). With this all this in mind and some Python knowledge, OpenKeyFlow was born! 

### FAQ

Q: Is OpenKeyFlow safe?
A: OpenKeyFlow is designed to be an offline, local-only Windows app. It does not auto update or reach the internet and th 

Q: Can I use it at work or school?
A: Absolutely. 

Q: Can I contribute?
A: Yes! Pull requests and feedback are welcome. Please follow the GPL v3 license.

Q: Will there be updates?
A: Definitely. I am one person on 
