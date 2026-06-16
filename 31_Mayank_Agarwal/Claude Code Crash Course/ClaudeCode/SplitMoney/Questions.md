## Installation & Setup FAQs

### ❓ What if the install command doesn't work?
- First: Check your internet connection.  
- Second: Run `claude doctor` — it’ll tell you what’s wrong.  
- Third: Make sure you have Node.js installed by running `node --version`.  

These three steps fix about 95% of install issues.

---

### ❓ I'm on Windows — should I use WSL?
WSL (Windows Subsystem for Linux) is great if you already use it.  
The Mac/Linux install command works perfectly inside WSL.

But you don’t need WSL — the native Windows PowerShell install works fine.  
👉 Use whatever you're comfortable with.

---

### ❓ I accidentally said "no" to trusting the folder. Now what?
Just close Claude Code and relaunch it from the same folder.  
It’ll ask again.

There’s no penalty for saying no — it’s a safety prompt, not a one-time decision.

---

### ❓ Which model should I start with?
- **Start with:** Sonnet 4.6 (default and best for learning)  
- **For saving money:** Switch to Haiku using `/model`  
- **For maximum capability:** Try Opus  

👉 Recommendation: Start with Sonnet — it’s the workhorse.

---

### ❓ Do I need Git installed?
No, you don’t need Git to use Claude Code.

However, if you already use Git, Claude Code can:
- Commit changes  
- Create branches  
- Work with your existing workflow  

For now, you can ignore Git — it’ll come up naturally during deployment.