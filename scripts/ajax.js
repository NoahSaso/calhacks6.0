function classes(elem) {
  return elem.className.split(' ');
}

function addClass(elem, c) {
  let cs = classes(elem);
  if (!cs.includes(c)) {
    cs.push(c);
  }
  elem.className = cs.join(' ');
}

function removeClass(elem, c) {
  let cs = classes(elem);
  if (cs.includes(c)) {
    cs.splice(cs.indexOf(c), 1);
  }
  elem.className = cs.join(' ');
}

function enable(elem) {
  removeClass(elem, 'disabled');
}

function disable(elem) {
  addClass(elem, 'disabled');
}

function send(file, encode) {
  let formData = new FormData();
  formData.append('encode', encode);
  formData.append('image', file);

    const secretTextElem = document.getElementById('secrettext');
    
  // const passphrase = document.getElementById('passphrase').value;

  // formData.append('publicKey', publicKey);
  if (encode) {
    formData.append('secretText', secretTextElem.value);
  } else {
      passphrase = prompt("Enter your private key password please.");
    // formData.append('privateKey', privateKey);
    formData.append('passphrase', passphrase);
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

  const encodeButton = document.getElementsByTagName('button')[0];
  const decodeButton = document.getElementsByTagName('button')[1];

  req.open('POST', '/submit', true);
  req.onreadystatechange = function () {
    switch (req.readyState) {
      case 3: // LOADING
        console.log('Loading...');
        break;
      case 4: // DONE
        const response = JSON.parse(req.response);
        console.log('DONE', req.status, response);
        const msg = response.message;
        if (req.status === 200) {
          if (encode) {
            alert(msg);
          } else {
	      // TODO(zeke): toggle(result) and then
	      //	      toggle('itemlist');
	      alert(msg);
            secretTextElem.value = msg;
          }
        } else {
          alert('Error: ' + msg);
        }
        enable(encodeButton);
        enable(decodeButton);
        break;
      default:
        break;
    }
  }

  disable(encodeButton);
  disable(decodeButton);

  req.send(formData);
  console.log('Sent');
}

function submit(encode) {
  const imageBase = document.getElementById('fileupload');
  const file = imageBase.files[0];
  send(file, encode);
}
