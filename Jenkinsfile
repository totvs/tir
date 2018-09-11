pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Building..'
                bat 'start cmd.exe /c scripts\\install_package.cmd'
                bat 'start cmd.exe /c %repos%\\testgrounds\\appserverkiller.cmd'
                bat 'start cmd.exe /c %repos%\\testgrounds\\appserverstarter.cmd'
            }
        }
        stage('Test') {
            steps {
                echo 'Testing..'
				sh 'python MATA030TESTSUITE.py'
				sh 'python MATA410TESTSUITE.py'
            }
        }
    }
}
