# AWS Profile Quick Tip

## TL;DR

```bash
# Create profile for this course
aws configure --profile course

# Use it (temporary)
export AWS_PROFILE=course

# Use it (permanent)
echo 'export AWS_PROFILE=course' >> ~/.zshrc && source ~/.zshrc
```

---

## Why

Keep your existing AWS configurations separate while following course instructions exactly as written.

## How

### 1. Create a dedicated profile
```bash
aws configure --profile course
```
Enter your course AWS credentials when prompted.

### 2. Set it as active
**Temporary (current session):**
```bash
export AWS_PROFILE=course
```

**Permanent (add to shell config):**
```bash
echo 'export AWS_PROFILE=course' >> ~/.zshrc && source ~/.zshrc
```
*Use `~/.bashrc` or `~/.bash_profile` for other shells.*

### 3. Switch back when needed
```bash
unset AWS_PROFILE
```
This returns you to your default AWS profile.