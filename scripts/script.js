/*
 * UTILITY FUNCTIONS
 */

function hide(id) {
  removeClass(document.getElementById(id), 'show');
}

function show(id) {
  addClass(document.getElementById(id), 'show');
}

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

/*
 * MAIN
 */

var isEncoding = true;

function send() {
  const imageBase = document.getElementById('file');
  const file = imageBase.files[0];

  let pubkey = document.getElementById('pubkey').files[0];
  let prvkey = document.getElementById('prvkey').files;
  if (prvkey.length > 0) {
    prvkey = prvkey[0];
  } else {
    prvkey = '';
  }

  let formData = new FormData();
  formData.append('encode', isEncoding);
  formData.append('image', file);
  formData.append('pubkeyfile', pubkey);
  formData.append('prvkeyfile', prvkey);

  const textElem = document.getElementById('text');
  formData.append(textElem.getAttribute('key'), textElem.value);

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

  const buttons = document.getElementsByTagName('button');
  const encodeButton = buttons[0];
  const decodeButton = buttons[1];

  req.open('POST', '/submit', true);
  req.onreadystatechange = function () {
    switch (req.readyState) {
      case 3: // LOADING
        console.log('Loading...');
        break;
      case 4: // DONE
        hide('loading');
        const response = JSON.parse(req.response);
        console.log('DONE', req.status, response);
        const msg = response.message;
        if (req.status === 200) {
          if (isEncoding) {
            alert(msg);
          } else {
            document.getElementById('decoded-output-text').value = msg;
            show('decoded-output');
            window.scrollTo(0, document.body.scrollHeight);
          }
        } else {
          alert('Error: ' + msg);
        }
        break;
      default:
        break;
    }
  }

  req.send(formData);
  show('loading');
}

function setIsEncoding(flag, elem) {
  const textElem = document.getElementById('text');

  if (flag !== isEncoding) {
    hide('select-image');
    hide('select-prvkey');
    hide('enter-text');
    hide('action');
    hide('loading');
    hide('decoded-output');

    textElem.value = '';
    document.getElementById('decoded-output-text').value = '';
    document.getElementById('pubkey').value = '';
    document.getElementById('prvkey').value = '';
  }

  const encodeButton = document.getElementsByTagName('button')[0];
  const decodeButton = document.getElementsByTagName('button')[1];

  isEncoding = flag;
  addClass(flag ? encodeButton : decodeButton, 'highlight');
  removeClass(flag ? decodeButton : encodeButton, 'highlight');

  const enterTextLabel = document.getElementById('enter-text-label');

  enterTextLabel.innerHTML = isEncoding ? 'Enter the secret text.' : 'Enter your private key passphrase.';
  textElem.setAttribute('key', isEncoding ? 'secretText' : 'passphrase');

  // Update the select keys stuff
  //    if ( isEncoding )
  //	doccument.getElementById("select-keys-text").innerHTML = "Select the public key of the receiver";
  if (!isEncoding) {
    show('select-prvkey');
  }
  show('select-keys');
}

// KeySelected should only fire after both
var keySelected = function() {
  let privSelected = false;
  let pubSelected = false;
  return function (keytype) {
    if (keytype === "public") {
      pubSelected = true;
    }
    if (keytype === "private") {
      privSelected = true;
    }
    if ((privSelected && pubSelected) || (pubSelected && isEncoding)) {
      show('select-image');
      privSelected = false;
      pubSelected = false;
    }
  };
}();

function copyOutput() {
  const outputElem = document.getElementById('decoded-output-text');
  outputElem.disabled = false;

  outputElem.select();
  outputElem.setSelectionRange(0, outputElem.value.length); // Mobile

  document.execCommand('copy');
  outputElem.disabled = true;
}

/*
 * HTML Event Handlers
 */

function fileSelected() {
  show('enter-text');
}

function textUpdated(elem) {
  (elem.value && elem.value.length ? show : hide)('action');
}
