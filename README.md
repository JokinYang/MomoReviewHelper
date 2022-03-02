# 墨墨复习助手
[![](https://img.shields.io/static/v1?label=%E6%95%88%E6%9E%9C%E5%B1%95%E7%A4%BA&message=GitHub%20Pages&color=blue)](https://blog.5p2o.com)  
使用android测试自动化的方式来收集[墨墨背单词](https://www.maimemo.com/) 当天规划记忆的单词,以供复习使用.  
# Why  
墨墨背单词所提供的复习方法较为单一, 且不能同时使用`看英文回忆中文`和`看中文回忆英文`来记忆单词. 
在我的日常使用过程中, 发现若使用`看中文回忆英文`会导致仅可根据中文拼写出英文, 单独看到英文单词却很难想起中文释义. 
所以就了这个项目.  
该项目会将当天记忆的单词以不直接显示中文解释的方式整理到[网页](https://blog.5p2o.com/20220101) 中, 来巩固由`英文`=>`中文`的记忆.
# How  
1. 借助[GitHub Actions](https://github.com/features/actions )提供的[Android虚拟环境](https://github.com/ReactiveCircus/android-emulator-runner) 来运行墨墨背单词(Android)软件, 
2. 使用Android自动化测试库([Airtest](https://github.com/AirtestProject/Airtest) , [uiautomator2](https://github.com/openatx/uiautomator2) 等), 来模拟人工登录帐号并抓取数据. 
3. 将抓取到的单词数据按照需要的方式生成网页, 发布到Github Pages上, 以供复习使用.
# Files
```
...
├── database.sqlite     # 存储单词信息的数据库文件
├── db_helper.py        # 操作数据库的工具文件
├── get_today_word.py   # 使用uiautomater2抓取当日单词的脚本
├── main.py             # 脚本入口, 尚未完善
├── page_maker.py       # 生成Github Pages
├── parse_maimemo.py    # 主要逻辑(使用Airtest). 生成数据库, 抓取当日学习的单词等
└── requirements.txt    # 依赖库
```
# Known Issue 
airtest在Actions所提供Android虚拟机(实际上Android虚拟机是跑在MacOS上的)上进行自动化测试时, 会稳定出现adb断开连接的bug. 导致无法在Action中使用[parse_maimemo.py](https://github.com/JokinYang/MomoReviewHelper/blob/main/parse_maimemo.py)  
在尝试后发现uiautomator2并不会出现上述问题, 故使用[get_today_word.py](https://github.com/JokinYang/MomoReviewHelper/blob/main/get_today_word.py) 来抓取每日学习的单词
# For Development
该README仅做简短的介绍, 若对项目有兴趣或在使用中遇到问题, Feel free to file a [Issue](https://github.com/JokinYang/MomoReviewHelper/issues/new )
