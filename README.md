# Clod Soul

A Codex plugin that automatically injects [SOUL.md](SOUL.md) into every session.
The soul favors reuse, minimal complexity, root-cause fixes, proportionate
verification, and concise, natural communication.

## Install

Once this plugin is available in your personal marketplace:

```sh
codex plugin add clod-soul@personal
```

You can also install it from the Personal marketplace in the Codex app.
Start a new thread after installation. No skill invocation or global `AGENTS.md`
changes are required.

## Behavior

Native `SessionStart` hooks inject the complete soul at startup, resume, clear,
and after compaction. A `SubagentStart` hook injects it into subagents too.
The hook reads `SOUL.md` from the installed plugin using `PLUGIN_ROOT`.
It runs `cat` and needs a shell with that command available.

The hooks use a 6,000-token context threshold to accommodate the soul. Keep the
document below that threshold when editing; larger hook output may be replaced
with a preview. See the [Codex hooks documentation](https://learn.chatgpt.com/docs/hooks).

The guidance is always loaded while the plugin is enabled. Coding workflows apply
to software tasks; simplicity, evidence, and communication principles also apply
to other work. User instructions and applicable safeguards still take precedence.

To uninstall:

```sh
codex plugin remove clod-soul@personal
```

## Local development

The development repository is separate from the personal marketplace's source
checkout at `~/plugins/clod-soul`. On this host that checkout is cloned from
`~/src/PERSONAL/clod-soul`. Commit changes in the development repository, then:

```sh
git -C "$HOME/plugins/clod-soul" pull --ff-only
codex plugin add clod-soul@personal
```

Change the manifest version for a release, or use Codex's plugin-creator
cachebuster helper before committing a development update, so reinstall picks up
new contents. Start a new thread after reinstalling.

For another installation, register the plugin in that user's marketplace using
Codex's plugin-creator workflow, then install with `codex plugin add`.
The [plugin manifest](.codex-plugin/plugin.json), `SOUL.md`, and `hooks/` form the
installable package. No skills are shipped.

## Origin

Adapted from [crypdick's lazy soul gist](https://gist.github.com/crypdick/7b7e21e8571b7cecf78737e8387b4b15),
with revisions for fewer approval interruptions, evidence-based debugging,
maintainability, natural language, and software-task scoping.
