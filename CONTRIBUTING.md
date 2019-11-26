## Dev Requirements

- pytest
- pytest-cov
- coverage
- flake8
- bumpversion

## Contribution Checklist

- All patches must be signed. [Signing Commits](#signing-commits)
- All contributed code must conform to flake8. [Code Style](#code-style)
- All new code contributions must be accompanied by a test.
    - Tests must pass and coverage remain above 90%. [Unit & Integration Tests](#unit-&-integration-tests)
- Follow Semantic Versioning. [Versions & Releases](#versions-&-releases)


## Versions & Releases

obs-img-utils adheres to Semantic versioning; see http://semver.org/ for details.

bumpversion is used for release version management, and is configured in
setup.cfg:

```
$ bumpversion major|minor|patch
$ git push
```

Bumpversion will create a commit with version updated in all locations.
The annotated tag is created separately.

```
$ git tag -a v{version}
# git tag -a v0.0.1

# Create a message with the changes since last release and push tags.
$ git push --tags
```

## Unit & Integration Tests

All tests should pass and test coverage should remain above 90%.

The tests and coverage can be run directly via pytest.

```
$ pytest --cov=obs_img_utils
```

## Code Style

Source should pass flake8 and pycodestyle standards.

```
$ flake8 obs_img_utils
```

## Signing Commits

The repository and the code base patches sent for inclusion must be GPG
signed. See the GitHub article,
[Signing commits using GPG](https://help.github.com/articles/signing-commits-using-gpg/),
for more information.
