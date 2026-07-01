# Mosaic — Setup Guide for Beginners

This guide assumes you know almost nothing about computers. That is totally fine. Follow each step exactly as written and you will have Mosaic running in about 15 minutes.

---

## Step 0: Before you start

**What you need:**
- A Mac computer (this guide is for Macs only)
- Your phone with WhatsApp open — you will scan a QR code
- A Gemini API key (a free code from Google) — [click here to get one](https://aistudio.google.com/apikey), then click "Create API Key" and copy the long string of letters and numbers

---

## Step 1: Open Terminal

Terminal is a text-based way to control your Mac. It looks scary but you only need to paste one thing.

1. Press `Command + Space` on your keyboard (both keys at the same time)
2. A search bar appears. Type: **Terminal**
3. Press **Enter**
4. A white or black window with text appears. You are now in Terminal.

---

## Step 2: Move to your Documents folder

In the Terminal window, type exactly this line and press **Enter**:

```bash
cd ~/Documents
```

(If it says "No such file", type `cd ~/Desktop` instead — your Documents folder might be named differently.)

---

## Step 3: Run the installer

Copy this entire line, paste it into Terminal, and press **Enter**:

```bash
curl -fsSL https://raw.githubusercontent.com/sameer-hoda/mosaic/main/install.sh | bash
```

Now wait. You will see lots of text scrolling by. This is normal. It is downloading and installing everything Mosaic needs. This takes 2-5 minutes depending on your internet speed.

---

## Step 4: What happens after the installer finishes

The installer will do these things automatically:
- Check if your computer has the right tools (Python, Node, Go)
- Install everything Mosaic needs
- Start all three parts of Mosaic (bridge, backend, frontend)
- Open your web browser to http://localhost:5173

**If your browser opens and you see a Mosaic page — skip to Step 7.**

**If something goes wrong — check the errors below.**

---

## Step 5: Set your Gemini API key

When the installer finishes, you need to tell Mosaic your Gemini key.

1. Open **Finder** (the blue face icon in your dock)
2. Go to **Documents** → **mosaic** → **taskdog-backend**
3. Find the file called **.env** (it might be hidden — if you cannot see it, press `Command + Shift + .` and hidden files will appear)
4. Double-click to open it (it opens in TextEdit)
5. You will see a line that says:
   ```
   GEMINI_API_KEY=your-gemini-api-key-here
   ```
6. Delete `your-gemini-api-key-here` and paste your actual Gemini key (the long code from Google)
7. It should now look like:
   ```
   GEMINI_API_KEY=AIzaSy...lots-of-letters-and-numbers...
   ```
8. Save the file (`Command + S`)
9. Close TextEdit

---

## Step 6: Restart Mosaic with your key

Go back to the Terminal window. Type:

```bash
cd ~/Documents/mosaic && bash scripts/start.sh
```

Press **Enter**. Wait 30 seconds. Your browser should open to the Mosaic page.

---

## Step 7: The Mosaic onboarding (3 steps)

### Page 1 — Enter your API key

You will see a page that says **"Step 1 of 3 · API Key"**.

1. There is a text box. Click inside it.
2. Paste your Gemini key (the same code from Step 5).
3. Click the **Validate** button.
4. If it says "Valid" — you are good. The page will automatically move to the next step.
5. If it says "Invalid" — your key is wrong. Go back to Google AI Studio and create a new one.

### Page 2 — Connect WhatsApp

You will see a page with a big QR code on it.

1. Open **WhatsApp** on your phone.
2. On iPhone: Go to **Settings** → **Linked Devices** → **Link a Device**.
3. On Android: Tap the **three dots** → **Linked Devices** → **Link a Device**.
4. Point your phone's camera at the QR code on your computer screen.
5. Your phone will beep/vibrate. The page on your computer will change.
6. You are now connected.

### Page 3 — Pick your groups

You will see a list of your WhatsApp chats and groups.

1. Click the **checkbox** next to each group or chat you want Mosaic to watch.
2. Choose the ones where people discuss tasks, commitments, or decisions.
3. Click **Continue** (or **Save**) at the top or bottom.
4. You will be taken to the **Dashboard**.

---

## Step 8: You are done! Next steps

On the Dashboard, click the **Discover** button. Mosaic will scan your chosen chats and find tasks, commitments, and decisions. This takes 1-2 minutes.

After that, your tasks appear as cards sorted by importance. To see more detail about any task, click on it.

---

## Stopping Mosaic

When you are done using Mosaic for the day:

1. Open Terminal
2. Type: `cd ~/Documents/mosaic && bash scripts/stop.sh`
3. Press Enter. Everything stops.

To start it again tomorrow: `cd ~/Documents/mosaic && bash scripts/start.sh`

---

## Expected Errors and How to Fix Them

### Error: "python3 — found 3.9 but need 3.10+"

Your Mac has an old Python. You need a newer one.

1. Open Terminal
2. Type this and press Enter:
   ```bash
   brew install python@3.12
   ```
3. Wait for it to finish (shows "already installed" or installs it).
4. Now run the installer again:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/sameer-hoda/mosaic/main/install.sh | bash
   ```

---

### Error: "go: command not found" or "brew: command not found"

Your Mac does not have the tools to install programs.

1. Open Terminal
2. Go to https://brew.sh — copy the long line of code on that page
3. Paste it in Terminal and press Enter. Wait for it to finish (5-10 minutes).
4. Then run:
   ```bash
   brew install go node python@3.12
   ```
5. After that finishes, run the installer again.

---

### Error: "502 Bad Gateway" when trying to validate API key

This means the backend (the part that talks to Google) did not start properly.

1. Open Terminal
2. Type: `cat /tmp/mosaic_backend.log`
3. Look at the last few lines. If you see the word "Error" or "Traceback", there is a problem with the code.
4. Try restarting: `cd ~/Documents/mosaic && bash scripts/start.sh`
5. If it still fails, delete the mosaic folder and start over:
   ```bash
   cd ~/Documents
   rm -rf mosaic
   curl -fsSL https://raw.githubusercontent.com/sameer-hoda/mosaic/main/install.sh | bash
   ```

---

### Error: "QR code won't scan"

1. Make sure your phone and computer are on the **same WiFi network**.
2. Try scanning closer or farther from the screen.
3. If the QR code looks frozen, click refresh on the page.
4. If nothing works, restart the bridge: `cd ~/Documents/mosaic && bash scripts/stop.sh && bash scripts/start.sh`

---

### Error: "No chats found" during group selection

This means WhatsApp has not loaded your chat list yet. Wait 30 seconds and refresh the page. If it still fails, restart your computer and try again.

---

### Error: The browser opens but shows a blank white page

1. Make sure Mosaic is actually running (Terminal should still be open and showing output).
2. Go to http://localhost:5173 in your browser (type it into the address bar).
3. If it still shows nothing, restart: `cd ~/Documents/mosaic && bash scripts/stop.sh && bash scripts/start.sh`

---

## Still stuck?

Ask the person who sent you this guide. They can help you with your specific error.
