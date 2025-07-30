import sys
import re


class MyVersion:
    def __init__(self, version_str: str):
        self.valid = True

        pattern = r"v(\d+)\.(\d+)\.(\d+)(-beta\.(\d+))?"
        ver_match = re.fullmatch(pattern, version_str)
        if not bool(ver_match):
            self.valid = False
            return

        x = ver_match.group(1)
        y = ver_match.group(2)
        z = ver_match.group(3)
        n = ver_match.group(5)

        self.x = int(x)
        self.y = int(y)
        self.z = int(z)
        self.n = int(n) if n is not None else None

    def is_beta(self) -> bool:
        return self.n is not None

    def bump_candidates(self) -> list["MyVersion"]:
        if not self.is_valid():
            return []

        candidates = []
        if self.n is not None:
            # Bump beta version
            candidates = [
                f"v{self.x}.{self.y}.{self.z}",
                f"v{self.x}.{self.y}.{self.z}-beta.{self.n + 1}",
            ]
        else:
            # Bump stable version
            candidates = [
                f"v{self.x}.{self.y}.{self.z+1}",
                f"v{self.x}.{self.y + 1}.0",
                f"v{self.x + 1}.0.0",
            ]
            candidates += [f"{candidate}-beta.1" for candidate in candidates]

        return [MyVersion(candidate) for candidate in candidates]

    def is_valid(self) -> bool:
        return bool(self.valid)

    def __eq__(self, other: "MyVersion") -> bool:
        if (
            not isinstance(other, MyVersion)
            or not self.is_valid()
            or not other.is_valid()
        ):
            return False
        return (self.x, self.y, self.z, self.n) == (other.x, other.y, other.z, other.n)

    def __lt__(self, other: "MyVersion") -> bool:
        if (
            not isinstance(other, MyVersion)
            or not self.is_valid()
            or not other.is_valid()
        ):
            raise NotImplementedError
        if self.x != other.x:
            return self.x < other.x
        if self.y != other.y:
            return self.y < other.y
        if self.z != other.z:
            return self.z < other.z
        return (self.n or 0) < (other.n or 0)

    def __str__(self) -> str:
        if not self.is_valid():
            return ""
        return f"v{self.x}.{self.y}.{self.z}{f'-beta.{self.n}' if self.n else ''}"


def main():
    if len(sys.argv) > 4 or len(sys.argv) < 2:
        print("Usage: check_tag.py NEW_TAG LATEST_TAG CUR_COMMIT_TAG")
        sys.exit(1)

    new_tag = sys.argv[1]
    latest_tag = sys.argv[2] if len(sys.argv) >= 3 else "v0.0.0"
    cur_commit_tag = sys.argv[3] if len(sys.argv) >= 4 else ""

    new_ver = MyVersion(new_tag)
    latest_ver = MyVersion(latest_tag)
    cur_ver = MyVersion(cur_commit_tag)

    if not latest_ver.is_valid():
        latest_ver = MyVersion("v0.0.0")

    # --- Rule 1: Check if NEW_TAG is valid
    if not new_ver.is_valid():
        print(
            f"Invalid version tag format: `{new_tag}`. "
            f"Expected format: `vX.Y.Z` or `vX.Y.Z-beta.N`."
        )
        return

    # --- Rule 2: Check if new commits exist
    if cur_ver.is_valid():
        if not cur_ver.is_beta():
            print(f"No updates since last stable release: `{cur_ver}`.")
            return
        if new_ver.is_beta() and cur_ver.is_beta():
            print(f"No updates since last beta release: `{cur_ver}`.")
            return

    # --- Rule 3: Check version bump correctness
    bump_candidates = latest_ver.bump_candidates()
    if new_ver not in bump_candidates:
        print(
            f"Invalid version bump: `{new_ver}`. "
            f"Expected one of: `{'`, `'.join(str(c) for c in bump_candidates)}`."
        )
        return

    print("Beta" if new_ver.is_beta() else "Stable")


if __name__ == "__main__":
    main()
