const path = require('path');

const CopyPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const webpack = require('webpack');

const DEV = process.env.NODE_ENV === 'development';

module.exports = {
  entry: {
    'main': './assets/js/index.js',
    'style': './assets/js/style.js'
  },
  output: {
    filename: '[name].js'
  },
  module: {
    rules: [
      {
        test: /\.scss$/,
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
            options: {
              hmr: DEV,
            }
          },
          'css-loader', 'sass-loader'
        ]
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
    // I use 3000 out of an old habit.
    port: 3000
  },

  output: {
    path: path.resolve(__dirname, 'html/resource/webpack/'),
    publicPath: '/resource/webpack/'
  },

  plugins: [
    new CopyPlugin({
      patterns: [
        {from: 'assets/images', to: path.resolve(__dirname, './html/resource/images')}
      ]
    }),
    new MiniCssExtractPlugin({
      filename: '[name].css'
    }),
    new webpack.HotModuleReplacementPlugin(),
  ]
}
