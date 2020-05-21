import os
import os.path as osp
import pandas as pd
import re
from tika import parser

removal_kwds = [
    'No Course Articulated',
    'Articulates as a Series Only',
    'Agreement Report',
    'Articulation Agreement by Department',
    'Effective during the',
    'Articulation subject to completion',
]
special_kwds = [
    '--- And ---',
    '--- Or ---'
]

def collapseLines(lines):
    lines = lines[:lines.index("END OF AGREEMENT")-1] # Skip last one - we don't need the subject here
    # Remove unecessary kwds
    i = 0
    while i < len(lines):
        l = lines[i]
        if any(l.startswith(p) for p in removal_kwds):
            lines.pop(i)
        else:
            i += 1

    # Collapse multiline course titles
    i = 0
    while i < len(lines):
        l = lines[i]
        if not re.match(r'^\w+[\s-]{1,2}[\d\w]+.*\s-', l) and all(not l.startswith(p) for p in special_kwds):
            lines[i-1] = lines[i-1] + ' ' + lines[i]
            lines.pop(i)
        else:
            i += 1


    #first collapse ands
    i = len(lines)-1
    while i > 0:
        l = lines[i]
        if l == '--- And ---':
            lines[i - 1] = lines[i - 1] + ' {AND} ' + lines[i + 1]
            lines.pop(i)
            lines.pop(i)
        i -= 1

    # collapse agreements
    i = len(lines) - 1
    while i > 0:
        l = lines[i]
        if l.startswith('←'):
            lines[i - 1] = lines[i - 1] + ' ' + lines[i]
            lines.pop(i)
        i -= 1

    # collapse or
    i = len(lines)-1
    while i > 0:
        l = lines[i]
        if l == '--- Or ---':
            lines[i - 1] = lines[i - 1] + ' {OR} ' + lines[i + 1]
            lines.pop(i)
            lines.pop(i)
        i -= 1

    return lines

def splitAndExtractAllCourseInfo(course_series):
    df = course_series.str.split(' ← ', expand=True)
    l = splitAndExtractCombinedCourseInfo(df[0])
    r = splitAndExtractCombinedCourseInfo(df[1])
    return l, r

def splitAndExtractCombinedCourseInfo(course_series):
    split_or = course_series.str.split(' {OR} ', expand=True)
    for c in split_or:
        col = split_or[c]
        split_and = col.str.split(' {AND} ', expand=True)
        for d in split_and:
            dol = split_and[d]
            split_and[d] = dol.apply(extractCourseInfo)
        agg_and = split_and.agg(lambda l: aggregator(l, ' && '), axis=1)
        split_or[c] = agg_and
    combined = split_or.agg(lambda l: aggregator(l, ' || '), axis=1)
    final = pd.DataFrame(combined.to_list(), columns=['Department', 'Number', 'Title', 'Units'])
    return final

def aggregator(lst, delim):
    new = []
    for i in range(4):
        concat = delim.join(l[i] for l in lst if l[i])
        new.append(concat)
    return new

def extractCourseInfo(course_title):
    if not course_title or course_title in removal_kwds:
        return ['', '', '', '']
    department = re.search(r'^(\w+)[\s-]{1,2}[\d\w]+.*\s-', course_title)[1]
    number = re.search(r'[\s-]{1,2}([\d\w]+.*)\s-', course_title)[1]
    name = re.search(r'-\s(.*)\s\(', course_title)[1]
    units = re.search(r'\(([.\d]*)\)', course_title)[1]
    return [department, number, name, units]


def extractArticulationAgreement(pdf):
    raw = parser.from_file(pdf)
    lines = raw['content'].splitlines()
    lines = [l.replace('\u200b', '') for l in lines if l]
    courses = collapseLines(lines)
    school_to = [l for l in lines if 'To: ' in l][-1]
    school_to_year = lines[lines.index(school_to)+1][:9]
    school_to = school_to[4:]
    school_from = [l for l in lines if 'From: ' in l][-1]
    school_from_year = lines[lines.index(school_from)+1][:9]
    school_from = school_from[6:]
    subject = lines[lines.index("END OF AGREEMENT")-1]
    df = pd.DataFrame({
        'SchoolTo': school_to,
        'SchoolToYear': school_to_year,
        'SchoolFrom': school_from,
        'SchoolFromYear': school_from_year,
        'Subject': subject,
        'Course': courses,
    })
    to, frum = splitAndExtractAllCourseInfo(df['Course'])
    df[['SchoolToCourseDept', 'SchoolToCourseNo', 'SchoolToCourseTitle', 'SchoolToCourseUnits']] = to
    df[['SchoolFromCourseDept', 'SchoolFromCourseNo', 'SchoolFromCourseTitle', 'SchoolFromCourseUnits']] = frum

    df = df.drop(columns='Course')
    return df

pdf_dir ='./pdfs/'
if not osp.isdir(pdf_dir):
    os.mkdir(pdf_dir)


_, _, files = next(os.walk(pdf_dir))
#a = extractArticulationAgreement(pdf_dir+[f for f in files if 'VENTURA' in f][0])
df = []
for i, f in enumerate(files):
    print(i)
    if f[-4:]=='.pdf':
        df.append(extractArticulationAgreement(pdf_dir+f))
df = pd.concat(df)
df = df.drop_duplicates()
df.to_csv("all.csv")