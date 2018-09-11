pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Building..'
                bat 'start %repos%\\testgrounds\\appserverkiller.cmd'
                bat 'start %repos%\\testgrounds\\appserverstarter.cmd'
                bat 'scripts\\install_package.cmd'
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
