# Distribution Guide - DeepDive Skill

## Overview

This guide covers how to distribute the DeepDive skill across multiple platforms.

## Current Status

✅ **GitHub Ready**: Repository structure complete
⏳ **Vercel Skill Lab**: Awaiting submission
✅ **Anthropic Skills**: Package ready (deepdive-v0.1.0.skill) - See SUBMISSION.md  
⏳ **Other Platforms**: Research phase

## Platform-Specific Distribution

### 1. GitHub (Primary Distribution)

**Status**: Ready to publish

**URL**: `https://github.com/tosi-n/deepdive`

**Installation Methods**:

```bash
# Method A: npx skills (for Claude Code, OpenCode)
npx skills add https://github.com/tosi-n/deepdive

# Method B: Direct git clone (universal)
git clone https://github.com/tosi-n/deepdive.git
cp -r deepdive ~/.config/<agent>/skills/

# Method C: GitHub releases (packaged .skill file)
curl -L https://github.com/tosi-n/deepdive/releases/download/v0.1.0/deepdive.skill
npx skills install deepdive.skill
```

**Files to Publish**:
- `SKILL.md` - Main skill file
- `references/` - Documentation modules
- `scripts/` - Python utilities
- `README.md` - User documentation
- `LICENSE` - MIT license

---

### 2. Vercel Skill Lab

**Status**: Need to submit

**URL**: https://vercel.com/marketplace/category/agents

**Prerequisites**:
- [ ] Vercel account (free tier ok)
- [ ] GitHub repository public
- [ ] `SKILL.md` with proper frontmatter
- [ ] No extraneous files in skill root

**Submission Steps**:

```bash
# 1. Ensure skill structure is correct
ls deepdive/
# Should show: SKILL.md, references/, scripts/

# 2. Submit via Vercel CLI (if available)
npm i -g vercel
vercel login
vercel skills submit ./deepdive

# OR submit via web form:
# https://vercel.com/marketplace/category/agents → "Submit Skill"
```

**Required Metadata**:
```yaml
# In SKILL.md frontmatter
---
name: deepdive
description: Universal data agent skill for natural language database querying, schema visualization, and automated chart generation. Use when working with PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, or Redshift databases, analyzing data, creating visualizations, exploring table structures, or needing data insights through natural language.
---
```

**Vercel Skill Requirements**:
- ✅ Single `SKILL.md` entry point
- ✅ Progressive disclosure (references/ folder)
- ✅ No README.md in skill root (moved to repo root)
- ✅ Scripts bundled for deterministic execution
- ✅ Clear trigger keywords in description

---

### 3. Anthropic Skills Registry

**Status**: Need to submit

**URL**: https://skills.sh

**Prerequisites**:
- [ ] GitHub account
- [ ] Public repository
- [ ] `.skill` package file

**Packaging**:

```bash
# Create .skill file (zip with .skill extension)
cd deepdive
zip -r ../deepdive.skill .

# Or using Claude's packaging script (if available)
python scripts/package_skill.py deepdive
```

**Submission**:

```bash
# Method A: Web form
# Go to https://skills.sh → "Submit Skill"
# Upload: deepdive.skill
# Fill: Name, Description, Tags, GitHub URL

# Method B: API (if available)
curl -X POST https://api.skills.sh/submit \
  -F "skill=@deepdive.skill" \
  -F "name=deepdive" \
  -F "description=Universal data agent skill"
```

**Tags for Discovery**:
- `database`
- `sql`
- `analytics`
- `visualization`
- `postgresql`
- `bigquery`
- `data-analysis`

---

### 4. Cursor IDE

**Status**: Manual installation only

**URL**: https://cursor.sh

**Installation**:

```bash
# Cursor uses same skill structure as Claude
# Copy skill to Cursor's skills directory

git clone https://github.com/tosi-n/deepdive.git
cp -r deepdive ~/.cursor/skills/

# Or use npx if Cursor supports it
npx skills add https://github.com/tosi-n/deepdive
```

**Note**: Cursor doesn't have a centralized marketplace yet. GitHub distribution is best.

---

### 5. OpenCode

**Status**: Ready for use

**URL**: https://opencode.ai

**Installation**:

```bash
# OpenCode uses same npx skills system as Claude
npx skills add https://github.com/tosi-n/deepdive

# Or manual:
git clone https://github.com/tosi-n/deepdive.git ~/.config/opencode/skills/deepdive
```

---

### 6. Other Agents

**Generic Installation**:

```bash
# Most agents supporting skills use this pattern:
SKILLS_DIR=~/.config/<agent-name>/skills  # Adjust path as needed
git clone https://github.com/tosi-n/deepdive.git $SKILLS_DIR/deepdive
```

**Agents to Research**:
- [ ] GitHub Copilot (custom instructions?)
- [ ] Continue.dev (open-source)
- [ ] Aider (open-source)
- [ ] Devin (if/when skills supported)
- [ ] Amazon CodeWhisperer (if skills available)

---

## Distribution Checklist

### Pre-Release

- [ ] All skill files created
- [ ] SKILL.md has proper YAML frontmatter
- [ ] References files are properly linked
- [ ] Scripts tested and working
- [ ] README.md comprehensive
- [ ] LICENSE file (MIT)
- [ ] .gitignore for .env files
- [ ] Example queries documented

### GitHub Release

- [ ] Create GitHub repository
- [ ] Push all files
- [ ] Create v0.1.0 release
- [ ] Attach .skill file to release
- [ ] Write release notes

### Vercel Submission

- [ ] Create Vercel account
- [ ] Submit skill to marketplace
- [ ] Wait for approval
- [ ] Update README with Vercel badge

### Anthropic Submission

- [ ] Package as .skill file
- [ ] Submit to skills.sh
- [ ] Wait for approval
- [ ] Update documentation

### Marketing

- [ ] Post on Twitter/X
- [ ] Share on LinkedIn
- [ ] Post on Hacker News ("Show HN")
- [ ] Share in relevant Discord/Slack communities
- [ ] Write blog post about use cases
- [ ] Create demo video/GIF

---

## Metrics to Track

**Distribution Metrics**:
- GitHub stars
- Skill installs (per platform)
- Documentation page views

**Usage Metrics**:
- Query frequency
- Database types used
- Visualization types generated
- Error rates

---

## Next Steps

1. **Publish to GitHub** (Today)
   - Create repo
   - Push files
   - Test installation

2. **Submit to Vercel** (This week)
   - Apply to marketplace
   - Await approval

3. **Submit to Anthropic** (This week)
   - Package skill
   - Submit form

4. **Promote** (Next week)
   - Social media posts
   - Blog article
   - Demo video

5. **Iterate** (Ongoing)
   - Collect feedback
   - Add features
   - Fix bugs
   - Update documentation

---

## Contact & Support

**GitHub Issues**: https://github.com/tosi-n/deepdive/issues

**Email**: tosi-n@stimulir.com

---

**Ready to distribute? Start with GitHub → Vercel → Anthropic!**
