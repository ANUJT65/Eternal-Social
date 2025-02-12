// Show popup message
function showPopupMessage(message) {
    const popup = document.getElementById('popup');
    popup.textContent = message;
    popup.classList.add('show');
    setTimeout(() => {
      popup.classList.remove('show');
    }, 3000);
  }
  
  // Preview the uploaded image
  function previewImage(event) {
    const imagePreview = document.getElementById('imagePreview');
    const file = event.target.files[0];
    if (file) {
      imagePreview.src = URL.createObjectURL(file);
      imagePreview.style.display = 'block';
    }
  }
  
  let myOrder = localStorage.getItem("myOrder") ? parseInt(localStorage.getItem("myOrder"), 10) : 1;
  let isProfessionalMode = false;
  // Variable to store the selected image file (if any)
  let selectedImageFile = null;
  
  document.getElementById('modeToggle').addEventListener('click', function() {
    isProfessionalMode = !isProfessionalMode;
    this.textContent = 'Empathy Mode: ' + (isProfessionalMode ? 'On' : 'Off');
  });
  
  const socket = new WebSocket(`ws://${window.location.hostname}:8000/ws/${Math.floor(Math.random()*10000)}`);
  
  function getProfilePic(message) {
    if (message.startsWith("YourOrder:")) return "";
    if (message.startsWith("You:")) return (myOrder % 2 === 0) ? "/wtf.png" : "/profile.png";
    else if (message.startsWith("Client #")) {
      const regex = /^Client #(\d+):/;
      const match = message.match(regex);
      if (match) {
        const clientNum = parseInt(match[1], 10);
        return (clientNum % 2 === 0) ? "/wtf.png" : "/profile.png";
      }
    }
    return "/profile.png";
  }
  
  function showMessage(message, className = '') {
    const container = document.getElementById('container');
    // Try parsing as JSON for image messages
    try {
      const msgObj = JSON.parse(message);
      if (msgObj.type === "image") {
        const wrapper = document.createElement('div');
        wrapper.className = "message-wrapper system";
        const img = document.createElement('img');
        img.src = msgObj.src;
        img.style.maxWidth = "200px";
        img.style.display = "block";
        img.style.margin = "0 auto";
        const caption = document.createElement('div');
        caption.textContent = msgObj.caption;
        caption.style.textAlign = "center";
        caption.style.marginTop = "5px";
        wrapper.appendChild(img);
        wrapper.appendChild(caption);
        container.appendChild(wrapper);
        container.scrollTop = container.scrollHeight;
        return;
      }
    } catch(e) {
      // Not an image message, continue
    }
    
    if (message.startsWith("YourOrder:")) {
      myOrder = parseInt(message.split(":")[1].trim(), 10);
      localStorage.setItem("myOrder", myOrder);
      console.log("Assigned order:", myOrder);
      return;
    }
    if (className.includes("system")) {
      const sysElem = document.createElement('div');
      sysElem.textContent = message;
      sysElem.className = "system";
      container.appendChild(sysElem);
      container.scrollTop = container.scrollHeight;
      return;
    }
    const wrapper = document.createElement('div');
    wrapper.className = "message-wrapper " + className;
    const img = document.createElement('img');
    img.src = getProfilePic(message);
    img.alt = "Profile Picture";
    const msgElem = document.createElement('div');
    msgElem.textContent = message;
    msgElem.className = "message " + className;
    wrapper.appendChild(img);
    wrapper.appendChild(msgElem);
    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
  }
  
  socket.addEventListener('open', () => {
    showMessage('Connected to chat', 'system');
  });
  
  socket.addEventListener('message', (event) => {
    const message = event.data;
    console.log("Message received from server:", message);
    // Try to parse as JSON for image messages
    try {
      const parsed = JSON.parse(message);
      if (parsed.type === "image") {
        showMessage(message);
        return;
      }
    } catch(e) {
      // Not an image message, continue
    }
    if (message.startsWith("YourOrder:")) {
      showMessage(message, "");
    } else if (message.startsWith('You:')) {
      showMessage(message, 'personal');
    } else if (message.startsWith('Client #')) {
      showMessage(message, 'received');
    } else {
      showMessage(message, 'system');
    }
  });
  
  socket.addEventListener('close', () => {
    showMessage('Connection closed', 'system');
  });
  
  const inputText = document.getElementById('inputText');
  const submitButton = document.getElementById('submitButton');
  
  function sendTextMessage() {
    const text = inputText.value.trim();
    const ethAddress = document.getElementById('ethAddress').value.trim();
    if (text && ethAddress) {
      socket.send(JSON.stringify({
        text: text,
        mode: isProfessionalMode ? 'professional' : 'standard',
        ethAddress: ethAddress
      }));
      inputText.value = '';
    } else {
      showMessage('Please enter both a message and your Ethereum address', 'system');
    }
  }
  
  // When the send arrow button is pressed, check if an image is selected
  submitButton.addEventListener('click', () => {
    const ethAddress = document.getElementById('ethAddress').value.trim();
    if (!ethAddress) {
      showMessage('Please enter your Ethereum address', 'system');
      return;
    }
    if (selectedImageFile) {
      const formData = new FormData();
      formData.append("file", selectedImageFile);
      formData.append("ethAddress", ethAddress);
      // First, send the image to the /predict endpoint to get the prediction result.
      fetch('/predict', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(result => {
        const displayMsg = result.result || result.error;
        // Use FileReader to convert the image file to a base64 data URL.
        const reader = new FileReader();
        reader.onload = function(e) {
          const dataURL = e.target.result;
          // Build an image message object
          const imageMessage = {
            type: "image",
            src: dataURL,
            caption: displayMsg.toLowerCase() === "fake" ? "Deep Fake" : "Real"
          };
          // Send the image message as JSON via WebSocket
          socket.send(JSON.stringify(imageMessage));
        };
        reader.readAsDataURL(selectedImageFile);
        selectedImageFile = null; // Reset the file after sending
        document.getElementById('imagePreview').style.display = 'none';
      })
      .catch(error => {
        showMessage('Image upload failed: ' + error, 'system');
      });
    } else {
      sendTextMessage();
    }
  });
  
  inputText.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
      if (inputText.value.trim() !== "") {
        sendTextMessage();
      }
    }
  });
  
  // When the Upload Image (phone icon) button is clicked, trigger the hidden file input
  document.getElementById('uploadButton').addEventListener('click', function() {
    document.getElementById('uploadImage').click();
  });
  
  // Image upload handling: store the selected file, show a preview, and display a popup message
  document.getElementById('uploadImage').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
      selectedImageFile = file;
      previewImage(event);
      showPopupMessage(`Selected image: ${file.name}`);
    }
  });
  
  document.querySelectorAll('.sidebar-icon').forEach((icon, index) => {
    icon.addEventListener('click', () => {
      document.querySelectorAll('.sidebar-icon').forEach(i => i.classList.remove('active'));
      icon.classList.add('active');
      if (index === 0) {
        const ethAddress = document.getElementById('ethAddress').value.trim();
        if (!ethAddress) {
          showMessage('Please enter your Ethereum address to unregister', 'system');
          return;
        }
        fetch('/unregister', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ethAddress: ethAddress })
        })
        .then(response => response.json())
        .then(result => {
          let displayMsg = result.message || result.error;
          if (displayMsg.length > 200) {
            displayMsg = displayMsg.substring(0, 200) + '...';
          }
          showMessage(displayMsg, 'system');
        })
        .catch(error => {
          showMessage('Unregistration failed: ' + error, 'system');
        });
      }
    });
  });
  
  document.getElementById('registerButton').addEventListener('click', async () => {
    const ethAddress = document.getElementById('ethAddress').value.trim();
    if (!ethAddress) {
      showMessage('Please enter an Ethereum address', 'system');
      return;
    }
    try {
      const response = await fetch('/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ ethAddress })
      });
      const result = await response.json();
      let displayMsg = result.message || result.error;
      if (displayMsg.length > 200) {
        displayMsg = displayMsg.substring(0, 200) + '...';
      }
      showMessage(displayMsg, 'system');
    } catch (error) {
      showMessage('Registration failed: ' + error, 'system');
    }
  });