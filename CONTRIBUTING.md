# Contributing

In order to contribute to our project, be sure to take your time and read this document. It's a guide of an effective and easy way of how contribution should be done.

## Issues list

The issues list is the preferred place to [report bugs](#reporting-bugs), [request features](#feature-requests) and send [pull requests](#pull-requests)

## Reporting bugs

A bug is a demonstrable problem that is caused by the code in this repository. A well written bug report can help us identify the problem and solve it in a quick and effective way.

How to report bugs:

1. **Look for the _issue_** &mdash; check wether the issue is already identified and reported or not.

2. **Check if the _issue_ is already fixed** &mdash; try to reproduce the bug using the latest `master` or development branch.

3. **Isolate the problem** &mdash; create a [reduced test case](http://css-tricks.com/reduced-test-cases/).

A good bug report must contain all needed information to identify and solve its problem. It's advised to write in the most detailed way, including information about your environment, how to reproduce the bug, what browser, operational systems, databases, component versions are being used, what results you are expecting, etc. All these details will help the developers to identify and solve the reported bug.

E.g:

> A short title and a descriptive example of the problem
>
> A description of the problem and the environment details that it occurs. If possible, write the steps to reproduce the problem:
>
> 1. First step
> 2. Second step
> 3. Other steps and etc.
>
> `<url>` - a url to the reduced test case
>
> Any information you desire to share that is relevant for the problem's solution. Code lines, possible solutions and opinions about the issue can be written here.

## Method Names

We have a standard that we use for naming methods for internal and external use (user level).

For methods that are created for internal use and will not be exposed in the Main class, we can name them as follows, for example:
get_value_grid ()

For the methods that will be available for use by the user that are exposed in the Main class, name the method as follows, for example:
GetValueGrid ()

We reinforce the importance of naming the methods as described, so that we have a single standard in the project.

## Feature Requests

Requesting features is a great way to suggest ideas to the project. If your idea has the same objective and is in the scope of the project, then it's possible that it can be implemented. Include as much information as possible and explain us why it is relevant to the project.

## Pull Requests

Pull requests are really helpful. They must be in the project's scope and avoid unrelated commits.

**Ask us first** before starting to work on a pull request of great impact (e.g. big features, code refactory, changing language), as it will require many working hours and it might not be interesting for the developers to merge at the current phase of the project.

**Pull Request by funcionality** is necessary, this facilitates the analysis of impact that funcionality generate and also speeds approval proccess.

| WARNING: If your pull request doesn't meet the requirements mentioned above it can be closed.|
| --- |

Make sure to read the [Architecture](doc_files/ARCHITECTURE.md) document
to understand how the tool was designed.

The methods must have docstrings describing its functionality and usage, and if any, parameters, defaults and returns. e.g.:

```python
def sum_numbers(self, first_number, second_number = 0):
    '''
    This method returns the sum of two numbers.

    :param first_number: The First number to be added.
    :type first_number: int
    :param second_number: The Second number to be added. - **Default:** 0
    :type second_number: int

    :return: The sum of the first_number and the second_number.
    :rtype: int

    Usage:

    >>> self.sum_numbers(1,2)
    '''
    return first_number + second_number
```

The pull request must follow the code conventions (identation, comments, naming) that are currently being used.

**IMPORTANT**: When you submit any change you agree that your changes are now under the same license as the project itself.