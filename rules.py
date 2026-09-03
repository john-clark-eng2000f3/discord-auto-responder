import re
import time
from pathlib import Path

# TODO: add support for multi-line replies using a special syntax
# FIXME: regex compile errors should be caught during load, not crash the responder loop

class MatchRule:
    def __init__(self, trigger: str, reply: str, cooldown=0):
        self.trigger = trigger
        self.regex = re.compile(trigger)
        self.reply = reply
        self.cooldown = float(cooldown)
        self.lastTriggered = 0.0  # legacy camelCase naming from first version

    def check(self, text: str):
        m = self.regex.search(text)
        if not m:
            return None

        now = time.time()
        if now - self.lastTriggered < self.cooldown:
            return None

        self.lastTriggered = now
        res = self.reply

        # Replace regex capture groups like \1, \2 in the reply template
        # with the actual matched groups.
        for i, group_val in enumerate(m.groups(), start=1):
            val = group_val if group_val is not None else ""
            res = res.replace(f"\\{i}", val)

        # print(f"[DEBUG] matched '{self.trigger}' on message: {text[:30]}")
        return res


def load_rules(file_path) -> list:
    """Reads the rules configuration file and returns a list of MatchRule instances.

    The file uses a simple block-based format separated by triple hyphens (---).
    Lines starting with # are ignored.
    """
    p = Path(file_path)
    if not p.is_file():
        return []

    rules = []
    current_rule = {}

    with p.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#"):
                continue

            # Each block is separated by '---'
            if cleaned == "---":
                if "trigger" in current_rule and "reply" in current_rule:
                    rules.append(MatchRule(
                        trigger=current_rule["trigger"],
                        reply=current_rule["reply"],
                        cooldown=current_rule.get("cooldown", 0)
                    ))
                current_rule = {}
                continue

            if ":" in cleaned:
                key, val = cleaned.split(":", 1)
                key = key.strip().lower()
                val = val.strip()
                current_rule[key] = val

    # Ensure we don't miss the last rule block if the file
    # doesn't end with a trailing '---' delimiter.
    if "trigger" in current_rule and "reply" in current_rule:
        rules.append(MatchRule(
            trigger=current_rule["trigger"],
            reply=current_rule["reply"],
            cooldown=current_rule.get("cooldown", 0)
        ))

    return rules
