#!/usr/bin/env python3

import http.server
import json
import os
import ImNaza
import webbrowser

PORT = 8888
OUTPUT_FOLDER = './submissions/'
TEMP_SUFFIX = '_temp'
OUTPUT_SUFFIX = '_encoded'

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

class Handler(http.server.SimpleHTTPRequestHandler):
    def respond(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        response = json.dumps(data)
        self.wfile.write(response.encode())

    def do_POST(self):
        """Handles POST request with image data"""
        cl = int(self.headers.get('Content-Length'))
        data = self.rfile.read(cl)
        data_str = str(data).split('\\r\\n')

        encode = True

        for idx, line in enumerate(data_str):
            if 'name="encode"' in line:
                encode = data_str[idx + 2] == 'true'
            elif 'name="image"' in line:
                path = line.split('filename="')[1][:-1] # -1 removes right quote
                filename, ext = os.path.splitext(path)

                if ext[1:].lower() in ['jpg', 'jpeg']:
                    header = b'\xff\xd8'
                    header_offset = 0
                    tail = b'\xff\xd9'
                    tail_offset = 0
                elif ext[1:].lower() in ['png']:
                    header = b'PNG'
                    header_offset = -1
                    tail = b'IEND'
                    tail_offset = 4
                else:
                    self.respond(400, {
                        'message': "Filetype {0} not supported".format(ext[1:])
                    })
                    return

                tail_offset += len(tail)

                try:
                    start = data.index(header) + header_offset
                    end = data.index(tail, start) + tail_offset
                except ValueError:
                    print("Can't find image data!")
                    self.respond(400, {
                        'message': "Can't find image data :("
                    })
                    return
            elif 'name="secretText"' in line:
                secret_text = data_str[idx + 2]
            elif 'name="publicKey"' in line:
                public_key = data_str[idx + 2]
            elif 'name="privateKey"' in line:
                private_key = data_str[idx + 2]
            elif 'name="passphrase"' in line:
                passphrase = data_str[idx + 2]

        temp_filepath = OUTPUT_FOLDER + filename + TEMP_SUFFIX + ext
        output_filepath = OUTPUT_FOLDER + filename + OUTPUT_SUFFIX + ext

        with open(temp_filepath, 'wb') as f:
            f.write(data[start:end])

        status = 200

        if encode:
            try:
                ImNaza.sender_job(secret_text, temp_filepath, output_filepath, 'test_pub.asc')
                message = "File saved to: {0}".format(output_filepath)
            except Exception as e:
                status = 400
                message = str(e)

            os.remove(temp_filepath)

        else:
            # decode text from image

#            try:
            message = ImNaza.receiver_job(temp_filepath, 'test_pub.asc', 'test_priv.asc', passphrase)
#            except Exception as e:
#                status = 400
#                message = str(e)

            os.remove(temp_filepath)

        self.respond(status, { 'message': message })

server = http.server.HTTPServer(('', PORT), Handler)
print("Serving at port", PORT)
webbrowser.open("http://localhost:8888/")
try:
    server.serve_forever()
except (KeyboardInterrupt, EOFError):
    pass
print("\nShutting down")
server.server_close()
