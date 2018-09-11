pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Building..'
                bat 'start %repos%\\testgrounds\\appserverkiller.cmd'
                bat 'start %repos%\\testgrounds\\appserverstarter.cmd'
                bat 'python setup.py sdist'
                bat 'pip install -U dist/tir-0.1.tar.gz'
            }
        }
        stage('Test') {
            steps {
                echo 'Testing..'
				bat 'python %repos%\\MATA030TESTSUITE.py'
				bat 'python %repos%\\MATA410TESTSUITE.py'
            }
        }
    }
}
