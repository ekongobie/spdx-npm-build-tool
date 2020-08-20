let {PythonShell} = require('python-shell')

export function generate_spdx(cmd_args) {
  let options = {
    args: cmd_args,
  };
  const path = require( 'path' ).join( __dirname, '.', 'python_scripts/tool.py' )
  PythonShell.run(path, options, function (err, results) {
  console.log("Errors: ", err);
  })
}
