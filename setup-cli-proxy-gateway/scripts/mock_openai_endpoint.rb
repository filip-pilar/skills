#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "socket"

port = Integer(ARGV.fetch(0))
server = TCPServer.new("127.0.0.1", port)

trap("TERM") { server.close; exit }
trap("INT") { server.close; exit }

def respond(socket, status, payload)
  body = JSON.generate(payload)
  reason = status == 200 ? "OK" : "Bad Request"
  socket.write("HTTP/1.1 #{status} #{reason}\r\n")
  socket.write("Content-Type: application/json\r\n")
  socket.write("Content-Length: #{body.bytesize}\r\n")
  socket.write("Connection: close\r\n\r\n")
  socket.write(body)
end

loop do
  socket = server.accept
  request_line = socket.gets("\r\n")
  next socket.close unless request_line

  method, path, = request_line.split
  headers = {}
  while (line = socket.gets("\r\n"))
    break if line == "\r\n"

    name, value = line.split(":", 2)
    headers[name.downcase] = value.to_s.strip
  end

  body = socket.read(headers.fetch("content-length", "0").to_i)
  payload = body.empty? ? {} : JSON.parse(body)

  if method == "GET" && path == "/health"
    respond(socket, 200, { status: "ok" })
  elsif method == "POST" && path == "/v1/chat/completions"
    valid_auth = headers["authorization"] == "Bearer fake-upstream-api-key"
    valid_model = payload["model"] == "upstream-gpt"
    unless valid_auth && valid_model
      respond(socket, 400, { error: { message: "mock auth/model assertion failed" } })
      socket.close
      next
    end

    expected = body[/Reply with exactly ([A-Z0-9_]+)\./, 1] || "CUSTOM_ENDPOINT_OK"
    respond(socket, 200, {
      id: "chatcmpl-mock",
      object: "chat.completion",
      model: "upstream-gpt",
      choices: [{ index: 0, finish_reason: "stop", message: { role: "assistant", content: expected } }],
      usage: { prompt_tokens: 5, completion_tokens: 2, total_tokens: 7 }
    })
  else
    respond(socket, 400, { error: { message: "unsupported mock route #{method} #{path}" } })
  end
  socket.close
end
