class VisionChatAgent:

    def answer(self, question, object_counts):
        question = question.lower()

        # How many?
        if "how many" in question:
            for obj, count in object_counts.items():
                if obj in question:
                    return f"I can see {count} {obj}(s)."

            return "I couldn't find that object."

        # Do you see?
        elif "do you see" in question:
            for obj in object_counts:
                if obj in question:
                    return f"Yes, I can see {object_counts[obj]} {obj}(s)."

            return "No, I cannot see that object."

        # What do you see?
        elif "what do you see" in question:
            if not object_counts:
                return "I cannot see any known objects."

            response = "I can currently see "

            items = []

            for obj, count in object_counts.items():
                items.append(f"{count} {obj}(s)")

            response += ", ".join(items)

            return response + "."

        return "I don't know how to answer that yet."