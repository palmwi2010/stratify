"""Class to turn embeddings df into a response"""
from openai import OpenAI
import os
from dotenv import load_dotenv

class ChatEngine():
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Config
        self.api_key = os.getenv('OPENAI_KEY')
        self.client = OpenAI(api_key = self.api_key)
        
        # Initialize system prompt
        self.system_prompt = self.create_system_prompt()
        
        # Set root conversation history (to be able to reset it later) and a rolling conversation history
        self.conversation_history = [{"role": "system", "content": self.system_prompt}]
            

    def create_system_prompt(self):
        """Function to create the system prompt for the API"""
        
        return f"""You are a fitness coach here to answer questions from athletes on their training routines, training plans and goals. Be encouraging and supportive.
    Answer the athlete's questions using the context provided to personalize it for them. The context will provide information on their
    ten most recent activities. If the athlete asks a question unrelated to fitness, respond: 'Sorry, I can't help with that!'"""
    
    def create_context(self, activities = [], max_tokens = 500):
        """Function to create the context for the model based on the question asked"""
        
        # Don't do anything if no activities received
        if activities == "":
            return ""
        
        context_lines = []
        # Take last 10 activities
        for activity in activities[:10]:
            line = f"Completed {activity['type']} labelled {activity['name']} on {activity['date']} with distance {activity['distance_f']}, at a pace of {activity['pace']}."
            if activity['has_heartrate']:
                line += f"Average heartrate was {activity['average_heartrate']}bpm and max heartrate was {activity['max_heartrate']}bpm."
            context_lines.append(line)
            
        return "\n".join(context_lines)
        
        # Separate conversations with two new lines
        return "\n\n"
    
    
    def reset_chat(self):
        """Clear conversation history"""
        self.conversation_history = [{"role": "system", "content": self.system_prompt}]
    
    
    def generate_response(self, question, activities = [], model = "gpt-3.5-turbo", max_context_tokens = 500, max_output = 300):
        """Answer a question based on the most similar context from the dataframe texts"""

        # Create a context
        context = self.create_context(activities = activities, max_tokens = max_context_tokens)
        
        # Create new question_context line
        question_context = {"role": "user", "content": f"Context: {context}\n\n---\n\nQuestion: {question}\n\n---\n\Response: "}
        messages = self.conversation_history + [question_context]
        
        # Get chat response
        try:
            # Create a chat completion using the question and context
            response = self.client.chat.completions.create(
                model = model, messages = messages, temperature = 0.5, max_tokens = max_output)
            
            # Get answer
            answer = response.choices[0].message.content
            
            # Add question and response to conversation history
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({'role': 'assistant', "content": answer})
            
            return answer
        except Exception as e:
            print(e)
            return ""