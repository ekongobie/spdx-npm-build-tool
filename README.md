# NPM SPDX Plugin
How can we seamlessly generate spdx documents in packages via npm?


## Usage:

### Via github clone
- Clone this repo,
- From your command line , navigate to this project directory
- Once in this project directory, execute the following:
Say you want to scan the folder located at '~/Desktop/tests/bitbake/'
and want the generated spdx file to be named spdxfilename
Run:
`spdx-npm-build-tool '~/Desktop/tests/bitbake/' spdxfilename --tv`

Check in the folder ~/Desktop/tests/bitbake/, you have your generated spdx file with name spdxfilename.spdx

## Further work/improvements:
The tools repository returns an error when the spdx rdf file generation is attempted; so it fails. Once this is corrected in the tools-python repository, updates might be requires in our tool for it to function appropriately.
