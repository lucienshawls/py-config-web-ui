import sys
from packaging.version import Version, InvalidVersion


def is_valid(tag: str) -> bool:
    if not tag.startswith("v"):
        return False
    try:
        Version(tag[1:])
        return True
    except InvalidVersion:
        return False


def is_stable(tag: str) -> bool:
    try:
        v = Version(tag[1:])
        return not v.is_prerelease
    except InvalidVersion:
        return False


def is_newer(new_tag: str, old_tag: str) -> bool:
    try:
        return Version(new_tag[1:]) > Version(old_tag[1:])
    except InvalidVersion:
        return False


def main():
    args = sys.argv[1:]

    if len(args) == 1:
        tag = args[0]
        if not is_valid(tag):
            print("0")
        elif is_stable(tag):
            print("1")
        else:
            print("2")

    elif len(args) == 2:
        new_tag, compare_tag = args
        if not is_valid(compare_tag):
            print("1")
        else:
            print("1" if is_newer(new_tag, compare_tag) else "0")


if __name__ == "__main__":
    main()
