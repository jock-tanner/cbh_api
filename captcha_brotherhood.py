#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# This software is licensed under GNU Lesser General Public License:
#
#   https://www.gnu.org/copyleft/lesser.html
#
# (C) JT 2014 mailto:tanner.of.kha@gmail.com
#
# Using functions provided you can connect to Captcha Brotherhood server
# and use it in your programs by both means of solving captchas yourself and
# letting others solve captchas for you.
#
# This work was inspired by this project:
#
#   https://github.com/gidder/brotherhood-gui/
#
# Captcha Brotherhood official site:
#
#   http://www.captchabrotherhood.com/
#

import os, sys, time, md5, mechanize

def main(argv):
  print "No CLI by now"
  sys.exit(0)

browser = mechanize.Browser()
browser.set_handle_equiv(True)
browser.set_handle_robots(False)

api_host = 'http://www.captchabrotherhood.com/'
username = ''
password = ''
no_confirm = False
timeout = 80

#
# Returns an integer representation of user's balance in credits
# or None if something went wrong
#
def ask_credits():
  result = browser.open(api_host + 'askCredits.aspx?username=' + username + '&password=' + password + '&version=1.2.0')
  try:
    msg, credits = result.get_data().split('-')
  except ValueError:
    return None
  if msg == 'OK':
    return int(credits)
  else:
    return None

#
# This is a base function for a CBH interactive client, that puts a human being
# into captcha-solving matrix.
#
# 'solver' is a custom callback that actually do the job of asking user a question
# through any possible UI. It should be implemented in your code as follows:
#
#   def solver(captcha_image, answer):
#       ...
#       return solution
#
# Note that CBH operates in two modes: normal mode and confirmation mode.
# In normal mode you should solve the captcha. In confirmation mode you should
# judge another user's solution as 'TRUE', 'FALSE' or 'FRAUD' (intentionally false).
# Hence the arguments:
#
#   captcha_image -- file-like object, containing a captcha jpeg
#   answer        -- another user's answer in confirmation mode,
#                    None in normal mode
#
# The return value is a string, containing captcha's solution in normal mode, or
# one of the following keywords:
#
#   -- TRUE
#   -- FALSE
#   -- FRAUD
#
# in confirmation mode.
#
# This function, in turn, wraps CBH API calls (http requests, actually) and tracks
# captcha id.
#
def solve_captcha(solver):
  result = browser.open(api_host + 'getCaptcha2Solve.aspx?username=' + username + '&password=' + password + '&NoConfirmation=' + str(no_confirm) + '&sslc=0&version=1.2.0')
  try:
    msg, data = result.get_data().split('-')
  except ValueError:
    return 'Unexpected error getting captcha ID'
  if msg == 'OK':
    if data == 'No Captcha':
      return data
    if 'Confirmation:' in data:
      # CONFIRMATION mode
      try:
        _, captcha_id, answer = data.split(':')
      except ValueError:
        return 'Unexpected error getting captcha answer to confirm'
    else:
      # NORMAL mode
      captcha_id = data
      answer = None
  else:
    return 'Server\'s been asked for captcha to solve; their answer was: ' + msg
  result = browser.open(api_host + 'showcaptcha.aspx?captchaID=' + captcha_id + '&username=' + username + '&password=' + password)
  captcha_image = result.read()
  solution = solver(captcha_image, answer)
  if answer == None:
    # expecting full captcha solution from solver (NORMAL mode)
    result = browser.open(api_host + 'setcaptchaResult.aspx?username=' + username + '&password=' + password + '&captchaID=' + captcha_id + '&captchaAnswer=' +
                          urllib.urlencode(solution) + '&version=1.2.0&cCode=' + _name_encode(username))
  else:
    # expecting yes-no-fraud answer from solver (CONFIRMATION mode)
    result = browser.open(api_host + 'svcConfirmationAnswer.aspx?username=' + username + '&password=' + password + '&captchaID=' + captcha_id + '&result=' +
                          solution + '&version=1.2.0')
  return 'Solution was submitted; server\'s answer was: ' + result.get_data()

#
# Let the power of captcha-solving matrix help you in your routine tasks!
# This function gets file-like object containing JPEG image
# and returns solution or human-readable error
#
def submit_captcha(captcha_image):
  submit_path = api_host + 'sendNewCaptcha.aspx?username=' + username + '&password=' + password + '&captchaSource=cliPlugin&captchaSite=-1&timeout=' + str(timeout) + '&version=1.1.9'
  # the request is really weird: image/jpeg camouflaged as a text/html...
  # looks like it works only this way
  result = browser.open(mechanize.Request(submit_path, captcha_image.read(), {'Content-Type': 'text/html; charset=utf-8'}))
  try:
    msg, captcha_id = result.get_data().split('-')
  except ValueError:
    return 'Unexpected error sending captcha for solving'
  if msg != 'OK':
    return 'Captcha was send; Server answered with: ' + msg
  status = ''
  # it may take time
  while status != 'answered':
    try:
      result = browser.open(api_host + 'askCaptchaResult.aspx?username=' + username + '&password=' + password + '&captchaID=' + captcha_id + '&version=1.1.9')
      time.sleep(2)
      _, status, solution = result.get_data().split('-')
    except ValueError:
      return 'Unexpected error queueing for solution'
  return 'Solution is ' + solution

#
# CBH can has kriptogriefy pleeeeeese
#
def _name_encode(text):
  code = text.strip() + 'CBH'
  code = md5(code.encode()).hexdigest()
  return code[-8:]

#
# main() centinel
#
if __name__ == "__main__":
  main(sys.argv)

