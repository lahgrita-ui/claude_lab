---
name: commit_msg
description: this skill add a score between 0 and 100 rigth after type: that punctuates the dificulty level required for code review, score is based on  2 way index, number of files changed, number of lines changed.
---

Based on read time add a score between 0 and 100 rigth after type: that punctuates the dificulty level required for code review, score is based on  2 way index, number of file changed, number of lines changed.
For instance if the required time is less than 1 minute, the score is 0, if the required time is more than 10 minutes, the score is 100, if the required time is between 1 and 10 minutes, the score is calculated as follows: (required time - 1) * 10. For example, if the required time is 5 minutes, the score is (5 - 1) * 10 = 40. The score is added right after type: in the commit message.
Whenever a user request to commit changes you must suggest a commit descriptive commit message and add the score right after type: in the commit message. The commit message should be descriptive and provide context for the changes made. The score should be based on the number of files changed and the number of lines changed, as well as the estimated time required to review the changes.
