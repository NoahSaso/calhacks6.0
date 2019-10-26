#!/usr/bin/env python3

import http.server
import json
import os

PORT = 8888
OUTPUT_FOLDER = './submissions/'
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
            if 'name="image"' in line:
                filename = line.split('filename="')[1][:-5] # -5 removes right quote and .jpg

                header = b'\xff\xd8'
                tail = b'\xff\xd9'

                try:
                    start = data.index(header)
                    end = data.index(tail, start) + 2
                except ValueError:
                    print("Can't find JPEG data!")
                    self.respond(400, {
                        'message': "Can't find JPEG data :("
                    })
                    return
            elif 'name="secretText"' in line:
                secret_text = data_str[idx + 2]
            elif 'name="publicKey"' in line:
                public_key = data_str[idx + 2]
            elif 'name="privateKey"' in line:
                private_key = data_str[idx + 2]
                encode = False

        if encode:
            output_filepath = OUTPUT_FOLDER + filename + OUTPUT_SUFFIX + '.jpg'

            with open(output_filepath, 'wb') as f:
                f.write(data[start:end])

            message = "File saved to: {0}".format(output_filepath)
        else:
            # decode text from image
            message = 'test123'

        self.respond(200, {
            'message': message
        })

server = http.server.HTTPServer(('', PORT), Handler)
print("Serving at port", PORT)

try:
    server.serve_forever()
except (KeyboardInterrupt, EOFError):
    pass
print("\nShutting down")
server.server_close()
