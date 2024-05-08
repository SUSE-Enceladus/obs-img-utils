v1.3.0 (2024-05-08)
===================

- Do not raise if image metadata not found unless conditions are provided
- Cleanup tests and rename setup method
- Update readthedocs config file

v1.2.0 (2023-03-06)
===================
- Adds new required extension (vmdk.xz) for images
- In case base_name variable is not set, the highest version-release combination of matching images in OBS is chosen.

v1.1.0 (2023-01-26)
===================
- Adds .vhdfixed extension support for images
- Supports new Open Build Service web interface
- Includes an --output parameter to packages subcommand to select output format
- Improvements in log verbosity control parameters (--quiet and --verbose)

v1.0.2 (2022-05-16)
===================

- Set conditions to empty list if no conditions
- Simplify the filter defaults using or condition

v1.0.1 (2022-05-06)
===================

- Move mkpath call to the init method
- Use a consistent return type of tuple in fetch_file_name function

v1.0.0 (2022-04-28)
===================

- Only check conditions if there are conditions to check
- Only download image metadata file if conditions exist or packages
  variable accessed
- Make packages a separate lazy variable so conditions methods can
  be called separately
- Pull base file name from image name instead of requiring image
  metadata file
- Make image version and release lazy properties instead of
  dictionary keys
- Checksum validation can be skipped
- Remove image_status dictionary and move remaining keys to
  instance variables
- Add check_all_conditions convenience method
- Add a function to fetch file name from download server based
  on regex match

v0.4.0 (2022-01-10)
===================

- Better handling for combined release and version conditions.

v0.3.2 (2021-12-17)
===================

- Add rpm-macros to build requirements in spec.

v0.3.1 (2021-10-18)
===================

- Fix spec to properly find the tarball.

v0.3.0 (2020-10-12)
===================

- Download signature file.
- Fix build requires in spec file.
- Handle xml report file from build service.

v0.2.0 (2020-04-06)
===================

- Add disallow license and package options.

v0.1.2 (2020-03-17)
===================

- Handle new checksum format from build service.

v0.1.1 (2019-12-20)
===================

- Remove man pages from source.
- Use explicit regex match for kiwi version.
- Handle multiple digit versions with kiwi version.

v0.1.0 (2019-11-20)
===================

- Allow expressive image conditions similar to package conditions.

v0.0.4 (2019-10-24)
===================

- Remove usr dir from spec.
- Account for content after checksum.

v0.0.3 (2019-07-10)
===================

- Release matches version.

v0.0.2 (2019-07-10)
===================

- No changes

v0.0.1 (2019-07-10)
===================

- Initial release.
