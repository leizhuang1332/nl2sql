# Long-Running Agent Harness Templates

Based on Anthropic's engineering methodology:
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

## Quick Start

To apply this harness to a new project:

```bash
# 1. Copy templates to your new project
cp -r .agent-harness/templates/* /path/to/new/project/

# 2. Customize the templates
# Edit feature_list.json with your project's features
# Edit progress.txt with your project info

# 3. Initialize git
cd /path/to/new/project
git init
git add -A
git commit -m "feat: initialize project with agent harness"
```

## File Structure

```
templates/
├── feature_list.json    # Feature list template
├── progress.txt         # Progress log template
├── init.sh             # Dev server startup script
└── prompts/
    ├── initializer_agent.md  # First session prompt
    └── coding_agent.md      # Subsequent sessions prompt
```

## Usage

### First Session (Initializer)
1. Read `prompts/initializer_agent.md`
2. Set up project structure
3. Create feature list
4. Make initial commit

### Subsequent Sessions (Coding Agent)
1. Read `progress.txt` + git log
2. Read `feature_list.json`
3. Choose one incomplete feature
4. Implement, test, commit
5. Update progress.txt

## Skill

This methodology is also available as an OpenCode skill:
`~/.config/opencode/superpowers/skills/long-running-agent/SKILL.md`
