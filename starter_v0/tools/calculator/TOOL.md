---
name: calculator
description: "Tính toán an toàn các biểu thức toán học hoặc thống kê số liệu."
parameters:
  type: object
  properties:
    expression:
      type: string
      description: "Biểu thức toán học cần tính (ví dụ: '150 * 1.2', '2 ** 10')"
  required: [expression]
---

# Calculator Tool
Tool thực hiện tính toán an toàn cho agent dựa trên AST parsing, không dùng eval() tùy tiện.
