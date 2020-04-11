Customizing Semantic-ui template
--------------------------------

````
# nodejs-legacy is needed for legacy symlinks, otherwise bower returns:
# /usr/bin/env: "node": No such file or directory
# deprecated:
#sudo apt install npm nodejs-legacy

export NODE_VERSION="node-v8.11.1-linux-x64"
pushd /opt
# LTS version
wget https://nodejs.org/dist/v8.11.1/$NODE_VERSION.tar.xz
# decompress it
tar xvf $NODE_VERSION.tar.xz
popd

# put it in the executables defaults environment path
export PATH=$PATH:/opt/$NODE_VERSION/bin:$PWD/node_modules/bower/bin:$PWD/node_modules/gulp/bin

# for future usage
source activate_npm.env

# https://bower.io/
# install js package manager
# sudo npm config set prefix /usr/local
npm install bower

# this will create a file called bower.json, in this we'll put our configuration/js-dependencies
# usefull if you have not yet created bower.json, otherwise just edit it
bower init

# gulp solves the problem of repetition, like:
#   Bundling and minifying libraries and stylesheets.
#   Refreshing your browser when you save a file.
#   Quickly running unit tests
#   Running code analysis
#   Less/Sass to CSS compilation
#   Copying modified files to an output directory
npm install gulp

# install semantic-ui bootstrap User Interface
npm install semantic-ui --save

# example with specific version
# bower install <package>#<version> --save

cd semantic

# Watching source files for changes
gulp.js watch

# build your UI from sources
gulp.js build
````
