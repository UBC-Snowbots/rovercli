#!/usr/bin/env bash

python_scripts_dir="$(python -c 'import sysconfig; print(sysconfig.get_path("scripts"))')" || {
    echo "Unable to determine the Python scripts directory." >&2
    return 1 2>/dev/null || exit 1
}

if [ ! -d "$python_scripts_dir" ]; then
    echo "Python scripts directory does not exist: $python_scripts_dir" >&2
    return 1 2>/dev/null || exit 1
fi

case "${SHELL##*/}" in
    zsh)
        shell_name="zsh"
        shell_rc="$HOME/.zshrc"
        ;;
    bash)
        shell_name="bash"
        shell_rc="$HOME/.bashrc"
        ;;
    *)
        if command -v zsh >/dev/null 2>&1; then
            shell_name="zsh"
            shell_rc="$HOME/.zshrc"
        elif command -v bash >/dev/null 2>&1; then
            shell_name="bash"
            shell_rc="$HOME/.bashrc"
        else
            echo "Neither zsh nor bash is available." >&2
            return 1 2>/dev/null || exit 1
        fi
        ;;
esac

path_entry="export PATH=\"$python_scripts_dir:\$PATH\""

case ":${PATH:-}:" in
    *:"$python_scripts_dir":*)
        ;;
    *)
        export PATH="$python_scripts_dir${PATH:+:$PATH}"
        ;;
esac

if ! grep -Fqx "$path_entry" "$shell_rc" 2>/dev/null; then
    printf '\n# Added by rovercli\n%s\n' "$path_entry" >> "$shell_rc" || {
        echo "Unable to update $shell_rc." >&2
        return 1 2>/dev/null || exit 1
    }
fi

echo "Added $python_scripts_dir to PATH in $shell_rc ($shell_name)."
echo "Restart your shell, or source $shell_rc, to use rovercli."
