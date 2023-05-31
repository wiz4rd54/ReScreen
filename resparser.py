import nltk 
import re
from datetime import datetime
import spacy
from spacy.matcher import PhraseMatcher

########################################
# FUNCTION TO CHECK THE FORMAT OF DATE #
########################################
def chk_date(string):
    pattern = r'^(?:Jan(?:\.)?(?:uary)?|Feb(?:\.)?(?:ruary)?|Mar(?:\.)?(?:ch)?|Apr(?:\.)?(?:il)?|May|Jun(?:\.)?(?:e)?|Jul(?:\.)?(?:y)?|Aug(?:\.)?(?:ust)?|Sept(?:\.)?(?:ember)?|Sep(?:\.)?(?:tember)?|Oct(?:\.)?(?:ober)?|Nov(?:\.)?(?:ember)?|Dec(?:\.)?(?:ember)?)\s+\d{4}$'
    match = re.match(pattern, string, re.IGNORECASE)
    return bool(match)

####################################################
# FUNCTION TO CALCULATE DIFFERENCE BETWEEN 2 DATES #
####################################################
def calculate_experience(start,end):
    try:
        start_date = datetime.strptime(start, "%b %Y")
        end_date = datetime.strptime(end, "%b %Y")
    except ValueError:
        start_date = datetime.strptime(start, "%B %Y")
        end_date = datetime.strptime(end, "%B %Y")
    duration = end_date - start_date
    total_years = duration.days / 365
    return total_years

#####################################################################
# FUNCTION TO CALCULATE THE TOTAL WORK EXPERIENCE THE APPLICANT HAS #
#####################################################################
def extract_workexperience(resume_text,minimum,maximum):
    resume_text = resume_text.split()
    list_of_headings = ['Address','Certificates','Contact','Objective','LinkedIn','Linkedin','Github','Phone','Mobile','Phone no.','Mobile No.','Email','E-mail','Skills','Skill','Summary','About me','Education','Languages','Techncial Skills','Interests','Organizations','Organisations','Personal Projects','Achievements']
    terms = ['Experience','Experiences','Responsibilities','Responsibility','Internships','Internship']

    # FINDING THE WORK EXPERIENCE SECTION
    experience = []
    for i in range(len(resume_text)):
        if resume_text[i] in terms or resume_text[i] in [x.upper() for x in terms]:
            flag = 0
            for j in range(i+1,len(resume_text)):
                if resume_text[j] in list_of_headings or resume_text[j] in [x.upper() for x in list_of_headings]:
                    flag = 1
                    break
                experience.append(resume_text[j])
            if flag == 1: break

    # FINDING THE DATES FROM THE WORK EXPERIENCE SECTION AND CALCULATING THE SCORE
    dates = []
    if experience:
        for i in range(len(experience)-2):
            if experience[i] == 'PRESENT' or experience[i] == 'Present' or experience[i] == 'present':
                now = datetime.now()
                string = now.strftime("%B %Y").upper()
            else:
                if '-' in experience[i]:
                    experience[i] = experience[i].replace('-', "")
                if '-' in experience[i+1]:
                    experience[i+1] = experience[i+1].replace('-', "")
                if "'" in experience[i]:
                    experience[i] = experience[i].replace("'", "20")
                if "'" in experience[i+1]:
                    experience[i+1] = experience[i+1].replace("'", "20")
                string = experience[i]+' '+experience[i+1]
            if chk_date(string):
                dates.append(string.capitalize())
        count = 0
        for i in range(0,len(dates),2):
            if '.' in dates[i]:
                dates[i] = dates[i].replace('.', "")
            if '.' in dates[i+1]:
                dates[i+1] = dates[i+1].replace('.', "")
            if 'Sept' in dates[i]:
                dates[i] = dates[i].replace('Sept', "Sep")
            if 'Sept' in dates[i+1]:
                dates[i+1] = dates[i+1].replace('Sept', "Sep")
            count = count + calculate_experience(dates[i],dates[i+1])
        count = round(count,2)

        # CALCULATING THE SCORE
        score = (count/maximum)*25
        if score>25:
            score = 25
        return score
    else:
        return 0

#################################################
# FUNCTION TO CALCULATE THE SCORE FOR EDUCATION #
#################################################
def extract_education(resume_text, requirements):

    # PREDEFINED FULL FORMS
    education_keywords = {
        'BCA':'bachelor of computer applications',
        'MCA':'master of computer applications',
        'BTech':'bachelor of technology',
        'MTech':'master of technology',
        'BSC':'bachelor of science',
        'MSC':'master of science',
        'BE':'bachelor of engineering',
        'ME':'master of engineering',
        'CE':'civil engineering',
        'CS':'computer science',
        'EE':'electrical engineering',
        'ME':'mechanical engineering',
        'IT':'information technology',
        'CSE':'computer science and engineering',
    }   
    resume_text = resume_text.split()
    list_of_headings = ['Address','Certificates','Contact','Objective','LinkedIn','Linkedin','Github','Phone','Mobile','Phone no.','Mobile No.','Email','E-mail','Skills','Skill','Experience','Experiences','Responsibilities','Responsibility','Internships','Internship','Summary','About me','Languages','Techncial Skills','Interests','Organizations','Organisations','Personal Projects','Achievements']
    terms = ['Education','Educational','Background','Academics','Qualifications']

    # FINDING THE EDUCATION SECTION
    education = []
    for i in range(len(resume_text)):
        if resume_text[i] in terms or resume_text[i] in [x.upper() for x in terms]:
            flag = 0
            for j in range(i+1,len(resume_text)):
                if resume_text[j] in list_of_headings or resume_text[j] in [x.upper() for x in list_of_headings]:
                    flag = 1
                    break
                education.append(resume_text[j])
            if flag == 1: break
    for i in range(len(education)):
        if education[i]=='B.' and education[i+1]=='Tech':
                education.append('BTECH')
        if education[i]=='M.' and education[i+1]=='Tech':
                education.append('MTECH')
    education = ' '.join(education)
    education = re.sub(r'[^a-zA-Z0-9 ]','',education)
    
    # FINDING THE DEGREE THE APPLICANT HAS
    applicant_edu = []
    for i in education_keywords.keys():
        if i in education or i.upper() in education or education_keywords[i] in education.lower():
            applicant_edu.append(i)
            applicant_edu.append(education_keywords[i])

    # CHECKING FOR BACHELORS AND MASTERS
    bachelors = 0
    masters = 0
    for i in applicant_edu:
        if i in ['BCA','BTech','BSC','']:
            bachelors = 1
        if i in ['MTech','MCA','MSC']:
            masters = 1
    
    # CHECKING IF THE REQUIREMENTS ARE MET OR NOT
    satisfied = 0
    for i in range(1,len(applicant_edu),2):
        if applicant_edu[i] in requirements.lower():
            satisfied = 1
            break
    
    # CALCULATING THE SCORE
    score = 0
    if satisfied==1 and bachelors==1 and masters==1:
        score = 25
    elif satisfied==1 and bachelors==1 and masters==0:
        score = 22.5
    
    return score

#############################################################
# FUNCTION TO CHECK FOR REQUIRED SKILLS IN THE USERS RESUME #
#############################################################
def extract_skills(resume_text,skills):
    nlp = spacy.load("en_core_web_sm")
    matcher = PhraseMatcher(nlp.vocab)
    
    patterns = [nlp.make_doc(skill) for skill in skills]
    matcher.add("TerminologyList", patterns)

    user_skills = []
    doc = nlp(resume_text)
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        user_skills.append(span.text)
    
    user_skills = list(set(user_skills))
    score = (len(user_skills)/len(skills))*50
    return score

###############################################
# FUNCTION TO GET THE APPLICANTS PHONE NUMBER #
###############################################
def extract_phone_numbers(resume_text):
    phone_number_pattern = r'\b((91)?\d{10}|(91)?\d{12}|\d{4}-\d{2}-\d{4}|\d{2}-\d{4}-\d{3}-\d{3}|\d{3}-\d{8})\b'
    phone_numbers = re.findall(phone_number_pattern, resume_text)
    if phone_numbers:
        return phone_numbers[0][0]
    else:
        return []

################################################
# FUNCTION TO GET THE APPLICANTS EMAIL ADDRESS #
################################################
def extract_email_addresses(resume_text):
    email_address_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
    email_addresses = email_address_pattern.findall(resume_text)
    if email_addresses:
        return email_addresses
    else:
        return []
    
#####################################################################
# FUNCTION TO GET THE APPLICANTS LINKEDIN AND GITHUB LINKS IT THERE #
#####################################################################
def extract_links(resume_text):
    linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/(?:in|profile)/[\w-]+/?'
    lines = resume_text.split('\n')
    resume_text = ''.join(lines)
    linkedin_links = re.findall(linkedin_pattern, resume_text)
    
    github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+(?:/[\w-]+)?(?:\.git)?/?'
    github_links = re.findall(github_pattern, resume_text)

    if linkedin_links or github_links:
        return linkedin_links+github_links
    else:
        return []

###########################################
# FUNCTION TO EXTRACT THE APPLICANTS NAME #
###########################################
def extract_names(resume_text):
    words = nltk.word_tokenize(resume_text)
    name = words[0]+' '+words[1]
    return name