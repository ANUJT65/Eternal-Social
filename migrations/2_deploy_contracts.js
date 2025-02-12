const NewsClassification = artifacts.require("NewsClassification");

module.exports = function (deployer) {
  deployer.deploy(NewsClassification);
};
