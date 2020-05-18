module.exports = {
  entry: {
    'main': './assets/js/index.js',
    // 'main-css': './src/css/index.css'
  },
  output: {
    filename: '[name].js'
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader', 'postcss-loader']
      },
      {
        test: /\.js$/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
          }
        }
      }
    ]
  },
  devServer: {
    contentBase: './html/',
    // Compression is mildly pointless in local dev.
    compress: false,
    // I use this port out of habit.
    port: 3000
  }
}
