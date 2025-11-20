from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def ai_chatbot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').lower()
            
            # Get student info for personalized responses
            student_courses = []
            if hasattr(request.user, 'studentprofile'):
                student_profile = request.user.studentprofile
                student_courses = [course.name.lower() for course in student_profile.courses.all()]
            
            # Enhanced AI responses with better keyword matching
            if any(word in user_message for word in ['hello', 'hi', 'hey', 'hola']):
                response = "Hello! 👋 How can I assist with your learning journey today?"
            
            elif any(word in user_message for word in ['progress', 'how am i doing', 'my progress']):
                response = "📊 Your progress is looking great! Based on your current pace, you're on track to complete your courses ahead of schedule. Keep up the excellent work! 🚀"
            
            elif any(word in user_message for word in ['python', 'python advanced', 'advanced python']):
                response = "🐍 **Python Advanced Topics:**\n• Decorators and generators\n• Context managers\n• Metaclasses\n• Concurrency (async/await)\n• Advanced OOP patterns\n\nWant specific examples or practice exercises?"
            
            elif any(word in user_message for word in ['web', 'web development', 'html', 'css']):
                response = "🌐 **Web Development Focus Areas:**\n• Responsive design with CSS Grid/Flexbox\n• JavaScript ES6+ features\n• React/Vue.js frameworks\n• REST APIs\n• Deployment strategies\n\nWhich area interests you most?"
            
            elif any(word in user_message for word in ['database', 'sql', 'mongodb']):
                response = "🗄️ **Database Concepts:**\n• SQL queries and optimization\n• Database normalization\n• Indexing strategies\n• NoSQL vs SQL\n• ACID properties\n\nNeed help with specific database problems?"
            
            elif any(word in user_message for word in ['help', 'what can you do']):
                response = "🆘 **I can help with:**\n• Course explanations\n• Study techniques\n• Project ideas\n• Code debugging\n• Learning roadmap\n• Motivation tips\n\nWhat specific help do you need?"
            
            elif any(word in user_message for word in ['study', 'how to study', 'learning tips']):
                response = "📖 **Effective Study Techniques:**\n• Pomodoro (25min study + 5min break)\n• Active recall practice\n• Spaced repetition\n• Teach what you learn\n• Build projects\n\nTry the Pomodoro technique today! ⏰"
            
            elif any(word in user_message for word in ['project', 'project ideas']):
                response = "💡 **Project Ideas:**\n• Personal portfolio website\n• Todo app with database\n• Weather app with API\n• Blog with user authentication\n• E-commerce site\n\nWhich project excites you?"
            
            elif any(word in user_message for word in ['thank', 'thanks']):
                response = "You're welcome! 😊 Remember: Consistent practice beats talent when talent doesn't practice. Keep coding! 💪"
            
            elif any(word in user_message for word in ['motivation', 'stuck', 'frustrated']):
                response = "💪 **Motivation Boost:**\nEvery expert was once a beginner. Your struggles today are building your expertise tomorrow. Take a break, then try again! 🌟"
            
            elif any(word in user_message for word in ['deadline', 'due', 'assignment']):
                response = "⏰ **Deadline Strategy:**\n1. Break task into smaller parts\n2. Set mini-deadlines\n3. Focus on one thing at a time\n4. Ask for help if stuck\n5. Review and submit early\n\nYou've got this! 🚀"
            
            else:
                # Check if message contains any course names
                course_keywords = ['python', 'web', 'database', 'javascript', 'html', 'css', 'react']
                found_course = None
                for keyword in course_keywords:
                    if keyword in user_message:
                        found_course = keyword
                        break
                
                if found_course:
                    if found_course == 'python':
                        response = f"🐍 Great question about Python! I recommend focusing on: functions, classes, error handling, and working with APIs. Want me to explain any specific Python concept?"
                    elif found_course == 'web':
                        response = f"🌐 Web development question! Key areas: HTML structure, CSS styling, JavaScript interactivity. Need help with frontend or backend?"
                    elif found_course == 'database':
                        response = f"🗄️ Database topic! Important concepts: SQL queries, relationships, normalization. Working with MySQL or MongoDB?"
                    else:
                        response = f"Interesting question about {found_course}! I'd love to help you with that. Could you be more specific about what you're trying to learn or build?"
                else:
                    response = "🤔 That's an interesting question! I'm here to help with your learning journey. Could you rephrase or ask about:\n• Specific courses\n• Study techniques\n• Project guidance\n• Code problems\n\nWhat would you like to explore?"
            
            return JsonResponse({'response': response})
            
        except Exception as e:
            return JsonResponse({'response': 'Sorry, I encountered an error. Please try again with a different question.'})
    
    return JsonResponse({'response': 'Please send a POST request with your message.'})