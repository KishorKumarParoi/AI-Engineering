with open("web/app.js", "r") as f:
    code = f.read()

# Check key anchors
assert "function renderClerkSignedInUI(profile)" in code
assert "function renderClerkSignedOutState()" in code

vip_functions = """
function setVipGatedState(isSignedIn) {
  const overlay = document.getElementById("vipGateOverlay");
  const bannerBtn = document.getElementById("btnHighlightTestVoice");
  const heroBtn = document.getElementById("btnHeroTestVoice");
  
  if (overlay) {
    if (isSignedIn) {
      overlay.classList.add("hidden");
    } else {
      overlay.classList.remove("hidden");
    }
  }

  if (bannerBtn) {
    if (isSignedIn) {
      bannerBtn.innerHTML = '<span>🎙️</span> Start Live Voice Call with Sofia';
      bannerBtn.onclick = () => {
        document.getElementById("voice-studio")?.scrollIntoView({ behavior: "smooth" });
        toggleVapiWebRTCCall();
      };
    } else {
      bannerBtn.innerHTML = '<span>✨</span> FREE TEST VOICE AI ASSISTANT';
      bannerBtn.onclick = () => openClerkSignUp();
    }
  }

  if (heroBtn) {
    if (isSignedIn) {
      heroBtn.innerHTML = '<span>🎙️</span> Talk with Sofia Live (WebRTC)';
      heroBtn.onclick = () => {
        document.getElementById("voice-studio")?.scrollIntoView({ behavior: "smooth" });
        toggleVapiWebRTCCall();
      };
    } else {
      heroBtn.innerHTML = '<span>✨</span> Free Test Voice AI Assistant';
      heroBtn.onclick = () => openClerkSignUp();
    }
  }
}

function handleHeroVoiceClick() {
  const user = getCachedVipUser();
  if (user) {
    document.getElementById("voice-studio")?.scrollIntoView({ behavior: "smooth" });
    toggleVapiWebRTCCall();
  } else {
    openClerkSignUp();
  }
}

function dismissLuxePreloader() {
  const preloader = document.getElementById("luxePreloader");
  if (preloader) {
    preloader.classList.add("fade-out");
    setTimeout(() => {
      preloader.style.display = "none";
    }, 450);
  }
}

if (document.readyState === "loading") {
  window.addEventListener("DOMContentLoaded", () => {
    setTimeout(dismissLuxePreloader, 350);
  });
} else {
  setTimeout(dismissLuxePreloader, 350);
}
"""

code = code.replace("function renderClerkSignedInUI(profile) {", vip_functions + "\nfunction renderClerkSignedInUI(profile) {")

old_clerk_signed_in = """  const hubStatus = document.getElementById("hubClerkStatus");
  if (hubStatus) {
    hubStatus.textContent = `🟢 Signed in (${email}${phone ? ' • ' + phone : ''})`;
    hubStatus.style.color = "var(--accent-emerald)";
  }

  loadTenantIntegrations("salon");
}"""

new_clerk_signed_in = """  const hubStatus = document.getElementById("hubClerkStatus");
  if (hubStatus) {
    hubStatus.textContent = `🟢 Signed in (${email}${phone ? ' • ' + phone : ''})`;
    hubStatus.style.color = "var(--accent-emerald)";
  }

  setVipGatedState(true);
  loadTenantIntegrations("salon");
}"""

assert old_clerk_signed_in in code, "old_clerk_signed_in not matched"
code = code.replace(old_clerk_signed_in, new_clerk_signed_in)

old_clerk_signed_out = """  const hubStatus = document.getElementById("hubClerkStatus");
  if (hubStatus) {
    hubStatus.textContent = "Clerk: Guest (Sign in to sync)";
    hubStatus.style.color = "var(--text-muted)";
  }
}"""

new_clerk_signed_out = """  const hubStatus = document.getElementById("hubClerkStatus");
  if (hubStatus) {
    hubStatus.textContent = "Clerk: Guest (Sign in to sync)";
    hubStatus.style.color = "var(--text-muted)";
  }

  setVipGatedState(false);
}"""

assert old_clerk_signed_out in code, "old_clerk_signed_out not matched"
code = code.replace(old_clerk_signed_out, new_clerk_signed_out)

with open("web/app.js", "w") as f:
    f.write(code)

print("web/app.js successfully updated!")
