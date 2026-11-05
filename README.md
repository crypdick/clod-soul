# Clod Soul

Converts Claude to Clod, a pragmatic caveman developer.

## Install

Claude Code:

```sh
claude plugin marketplace add crypdick/clod-soul && claude plugin install clod-soul@clod-soul
```

Codex:

```sh
codex plugin marketplace add crypdick/clod-soul && codex plugin add clod-soul@clod-soul
```

## Development and releases

Run `python3 -m unittest discover -s tests -v` before committing.
After checks pass for a push to `main`, CI increments the patch version and
pushes a `Release X.Y.Z` commit. `.claude-plugin/plugin.json` owns the version;
CI synchronizes `.codex-plugin/plugin.json` and the marketplace entry.
To choose a manual release, increase the version in `.claude-plugin/plugin.json`
before committing. CI preserves increases anywhere in the push. Feature branches
and pull requests run checks without releasing. Retries reuse the release commit,
and superseded pushes skip release.

The release job uses `GITHUB_TOKEN` with `contents: write`. Branch rules must
allow the bot to push. Bot pushes don't start another workflow run.

# Credits

Heavily inspired by [`juliusbrussee/caveman`](https://github.com/juliusbrussee/caveman) and [`dietrichgebert/ponytail`](https://github.com/dietrichgebert/ponytail).
