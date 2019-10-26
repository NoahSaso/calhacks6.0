function sendFile(file, includePrivateKey) {
  let formData = new FormData();
  formData.append('image', file);

  const publicKey = document.getElementById('publickey').value;
  const privateKey = document.getElementById('privatekey').value;

  formData.append('publicKey', publicKey);
  if (includePrivateKey) {
    formData.append('privateKey', privateKey);
  }

  let req = false;
  try {
    // Safari, Firefox, Opera 8+
    req = new XMLHttpRequest();
  } catch (e) {
    try {
      // Internet Explorer
      req = new ActiveXObject("Msxml2.XMLHTTP");
    } catch (e) {
      try {
        req = new ActiveXObject("Microsoft.XMLHTTP");
      } catch (e) {
        return false;
      }
    }
  }

  req.open('POST', '/submit', true);
  req.onreadystatechange = function () {
    console.log(req);
    switch (req.readyState) {
      case 3: // LOADING
        console.log('Loading...');
        break;
      case 4: // DONE
        const response = JSON.parse(req.response);
        console.log('DONE', response);
        break;
      default:
        break;
    }
  }

  req.send(formData);
  console.log('Sent');
}

function submit(includePrivateKey) {
  const imageBase = document.getElementById('fileupload');
  const file = imageBase.files[0];
  sendFile(file, includePrivateKey);
}
