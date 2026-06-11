import sympy as sp


def solve_math(query):
    try:
        expression = query.lower().replace("calculate", "").strip()

        # Handle percentages
        if "%" in expression and "of" in expression:
            percent, number = expression.split("of")

            percent = percent.replace("%", "").strip()
            number = number.strip()

            result = (float(percent) / 100) * float(number)
            return result

        result = sp.sympify(expression)
        return result

    except Exception:
        return "Sorry, I couldn't solve that."
        
        
def math_node(state):
    state["result"] = solve_math(state["query"])
    return state