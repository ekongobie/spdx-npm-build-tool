let {PythonShell} = require('python-shell')

let options = {
  args: process.argv
};

PythonShell.run('python_scripts/tool.py', options, function (err, results) {
console.log(err);
console.log(results);
console.log(process.argv);
})
