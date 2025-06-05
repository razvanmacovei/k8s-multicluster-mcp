#!/usr/bin/env node

/**
 * Generates Cursor deep link configurations for k8s-multicluster-mcp server
 */

const configs = [
  {
    name: "python3-basic",
    title: "Python3 Basic",
    config: {
      command: "python3",
      args: ["app.py"],
      env: {
        KUBECONFIG_DIR: "/path/to/your/kubeconfigs"
      }
    }
  },
  {
    name: "uv-local",
    title: "UV Package Manager",
    config: {
      command: "uv",
      args: ["--directory", ".", "run", "app.py"],
      env: {
        KUBECONFIG_DIR: "/path/to/your/kubeconfigs"
      }
    }
  },
  {
    name: "python3-absolute",
    title: "Python3 Absolute Path",
    config: {
      command: "python3",
      args: ["/path/to/k8s-multicluster-mcp/app.py"],
      env: {
        KUBECONFIG_DIR: "/path/to/your/kubeconfigs"
      }
    }
  }
];

function generateDeepLink(serverName, config) {
  const configString = JSON.stringify(config);
  const base64Config = Buffer.from(configString).toString('base64');
  return `cursor://anysphere.cursor-deeplink/mcp/install?name=${serverName}&config=${base64Config}`;
}

function generateMarkdownButton(title, deepLink) {
  return `[Add ${title} to Cursor](${deepLink})`;
}

console.log("# k8s-multicluster-mcp Deep Link Configurations\n");

configs.forEach((item, index) => {
  const deepLink = generateDeepLink("k8s-multicluster", item.config);
  const markdownButton = generateMarkdownButton(item.title, deepLink);
  
  console.log(`## ${index + 1}. ${item.title}`);
  console.log("");
  console.log("**Deep Link:**");
  console.log(deepLink);
  console.log("");
  console.log("**Markdown Button:**");
  console.log(markdownButton);
  console.log("");
  console.log("---");
  console.log("");
}); 